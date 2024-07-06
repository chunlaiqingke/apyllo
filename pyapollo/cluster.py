from random import shuffle
import requests
from concurrent.futures import ThreadPoolExecutor
import time
import schedule
import logging

'''
python 客户端支持集群
'''
class Cluster(object):
    
    def __init__(self, meta_url, ip) -> None:
        self.retries = 3
        self.timeout = 20
        self.sleep_time = 3
        self.meta_url = meta_url
        self.ip = ip
        self._configservices = []
        self._refresh()
        self._refreshPeriod()

    
    def getRandomConfigService(self):
        copy = list(self._configservices)
        shuffle(copy)
        return copy
        
    def getConfigService(self):
        url = f"{self.meta_url}/services/config"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                services = resp.json()
                return services
        except Exception as e:
            logging.error(e)
            return []
    
    def _refresh(self):
        for i in range(self.retries):
            services = self.getConfigService()
            if services:
                self._configservices = services
                return
            time.sleep(self.sleep_time)
            
    def _refreshPeriod(self):
        schedule.every(5).minutes.do(self._refresh)