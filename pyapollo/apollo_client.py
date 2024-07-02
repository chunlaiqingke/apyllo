# -*- coding: utf-8 -*-
import json
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import time

import requests

from change import ChangeListener, ConfigChange
from change import *
from cluster import Cluster

class ApolloClient(object):
    def __init__(self, app_id, cluster='default', config_server_url='http://localhost:8080', timeout=90, ip=None):
        self.config_server_url = config_server_url
        self.appId = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.stopped = False
        self.init_ip(ip)

        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1, 'test': -1, 'jsontest.json': -1}
        self.changes = []
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cluster = Cluster(self.config_server_url, self.ip)

    def init_ip(self, ip):
        if ip:
            self.ip = ip
        else:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 53))
                ip = s.getsockname()[0]
            finally:
                s.close()
            self.ip = ip

    # Main method
    def get_value(self, key, default_val=None, namespace='application', auto_fetch_on_cache_miss=False):
        if namespace not in self._notification_map:
            self._notification_map[namespace] = -1
            logging.getLogger(__name__).info("Add namespace '%s' to local notification map", namespace)

        if namespace not in self._cache:
            self._cache[namespace] = {}
            logging.getLogger(__name__).info("Add namespace '%s' to local cache", namespace)
            # This is a new namespace, need to do a blocking fetch to populate the local cache
            self._long_poll()

        if key in self._cache[namespace]:
            return self._cache[namespace][key]
        else:
            if auto_fetch_on_cache_miss:
                return self._cached_http_get(key, default_val, namespace)
            else:
                return default_val

    # Start the long polling loop. Two modes are provided:
    # 1: thread mode (default), create a worker thread to do the loop. Call self.stop() to quit the loop
    # 2: eventlet mode (recommended), no need to call the .stop() since it is async
    def start(self, use_eventlet=False, eventlet_monkey_patch=False, catch_signals=True):
        # First do a blocking long poll to populate the local cache, otherwise we may get racing problems
        if len(self._cache) == 0:
            self._long_poll_for_cluster()
        if use_eventlet:
            import eventlet
            if eventlet_monkey_patch:
                eventlet.monkey_patch()
            eventlet.spawn(self._listener)
        else:
            if catch_signals:
                import signal
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGABRT, self._signal_handler)
            t = threading.Thread(target=self._listener)
            t.start()

    def stop(self):
        self._stopping = True
        logging.getLogger(__name__).info("Stopping listener...")
        
    
    def _cached_http_get_for_cluster(self, key, default_val, namespace='application'):
        services = self.cluster.getConfigService()
        for service in services:
            try:
                self._cached_http_get(service, key, default_val, namespace)
                break
            except Exception as e:
                logging.getLogger(__name__).warn("Failed to get config from %s: %s" % (service, e))
        
        data = self._cache[namespace]

        if key in data:
            return data[key]
        else:
            return default_val
         

    def _cached_http_get(self, service, key, default_val, namespace='application'):
        url = '{}/configfiles/json/{}/{}/{}?ip={}'.format(service['instanceId'], self.appId, self.cluster, namespace, self.ip)
        r = requests.get(url)
        if r.ok:
            data = r.json()
            self._cache[namespace] = data
            logging.getLogger(__name__).info('Updated local cache for namespace %s', namespace)
        else:
            raise Exception('Failed to get config from %s' % service['instanceId'])


    def _uncached_http_get_for_cluster(self, namespace='application'):
        services = self.cluster.getConfigService()
        for service in services:
            try:
                self._uncached_http_get(service, namespace)
                break
            except Exception as e:
                logging.getLogger(__name__).warn("Failed to get config from %s: %s" % (service, e))
    

    def _uncached_http_get(self, service, namespace='application'):
        url = '{}/configs/{}/{}/{}?ip={}'.format(service['instanceId'], self.appId, self.cluster, namespace, self.ip)
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self._fireConfigChange(namespace, data['configurations'])
            self._cache[namespace] = data['configurations']
            logging.getLogger(__name__).info('Updated local cache for namespace %s release key %s: %s',
                                             namespace, data['releaseKey'],
                                             repr(self._cache[namespace]))
        else:
            raise Exception('Failed to get config from %s' % url)

    def _signal_handler(self, signal, frame):
        logging.getLogger(__name__).info('You pressed Ctrl+C!')
        self._stopping = True
        
    def _long_poll_for_cluster(self):
        services = self.cluster.getConfigService()
        for service in services:
            try:
                self._long_poll(service)
                break
            except Exception as e:
                logging.getLogger(__name__).warn("Long polling failed from %s: %s" % (service, e))
        time.sleep(self.timeout)

    def _long_poll(self, service):
        url = '{}/notifications/v2'.format(service['instanceId'])
        notifications = []
        for key in self._notification_map:
            notification_id = self._notification_map[key]
            notifications.append({
                'namespaceName': key,
                'notificationId': notification_id
            })

        r = requests.get(url=url, params={
            'appId': self.appId,
            'cluster': self.cluster,
            'notifications': json.dumps(notifications, ensure_ascii=False)
        }, timeout=self.timeout)

        logging.getLogger(__name__).debug('Long polling returns %d: url=%s', r.status_code, r.request.url)

        if r.status_code == 304:
            # no change, loop
            logging.getLogger(__name__).debug('No change, loop...')
            return

        if r.status_code == 200:
            data = r.json()
            for entry in data:
                ns = entry['namespaceName']
                nid = entry['notificationId']
                logging.getLogger(__name__).info("%s has changes: notificationId=%d", ns, nid)
                self._uncached_http_get(ns)
                self._notification_map[ns] = nid
        else:
            raise Exception('Long polling returns %d: url=%s', r.status_code, r.request.url)

    def _listener(self):
        logging.getLogger(__name__).info('Entering listener loop...')
        while not self._stopping:
            self._long_poll_for_cluster()

        logging.getLogger(__name__).info("Listener stopped!")
        self.stopped = True
        
        
    def add_change_listener(self, listener):
        self.changes.append(listener)

    def _fireConfigChange(self, namespaceName, newConfig):
        changes = self._realChanges(namespaceName, newConfig)
        if len(changes) > 0:
            self._notify_changes(ConfigChangeEvent(changes))
        
    
    def _notify_changes(self, changeEvent):
        for listener in self.changes:
            self.executor.submit(listener.onChange, (changeEvent))
            

    def _realChanges(self, namespaceName, newConfig):
        changes = self._calcPropertyChanges(namespaceName,self._cache.get(namespaceName), newConfig)
        realChanges = {}
        for change in changes:
            if change.namespace == namespaceName:
                realChanges[change.key] = change
                
        return realChanges
            
    '''
    计算变更的配置
    '''
    def _calcPropertyChanges(self, namespaceName, previewConfig, currentConfig):
        if not previewConfig:
            previewConfig = {}
        if not currentConfig:
            currentConfig = {}
            
        previewKeys = previewConfig.keys()
        currentKeys = currentConfig.keys()
        
        commonkeys = set(previewKeys).intersection(set(currentKeys))
        newKeys = set(currentKeys).difference(set(commonkeys))
        removeKeys = set(previewKeys).difference(set(currentKeys))
        
        changes = []
        
        for newkey in newKeys:
            changes.append(ConfigChange(namespaceName, newkey, None, currentConfig[newkey], ChangeType.ADD))
            
        for removekey in removeKeys:
            changes.append(ConfigChange(namespaceName, removekey, previewConfig[removekey], None, ChangeType.DELETE))
            
        for commonkey in commonkeys:
            newValue = currentConfig[commonkey]
            oldValue = previewConfig[commonkey]
            if newValue != oldValue:
                changes.append(ConfigChange(namespaceName, commonkey, oldValue, newValue, ChangeType.MODIFY))
                
        return changes


if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    client = ApolloClient('10001')
    
    listener = ChangeListener()
    listener.onChange = lambda event: print(f'onchange: {event.changes}')
    client.add_change_listener(listener)
    client.start()
    if sys.version_info[0] < 3:
        v = raw_input('Press any key to quit...')
    else:
        v = input('Press any key to quit...')

    client.stop()
    while not client.stopped:
        pass
