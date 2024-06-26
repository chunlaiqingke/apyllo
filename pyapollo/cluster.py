import requests
from concurrent.futures import ThreadPoolExecutor
import time
import schedule

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
        self.refresh()
    
    def getConfigService(self):
        return self._configservices
        
    def getConfigService(self):
        url = f"{self.meta_url}/services/config"
        resp = requests.get(url, timeout=self.timeout)
        if resp.status_code == 200:
            services = resp.json()
            return services
    
    def refresh(self):
        for i in range(self.retries):
            services = self.getConfigService()
            if services:
                self._configservices = services
            time.sleep(self.sleep_time)
        raise Exception("refresh config service failed")
            
    def refreshPeriod(self):
        schedule.every(2).minutes.do(self.refresh)