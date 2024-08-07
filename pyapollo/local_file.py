import platform
import os
from turtle import end_fill
import logging

class LocalFileRepository(object):
    """
    本地文件配置仓库
    访问降级
    """
    def __init__(self, appId, cluster) -> None:
        self.config_dir = "/apollo/config-cache"
        self.local_root_dir = ""
        self.appId = appId
        self.cluster = cluster
        
    def _isOSWindow(self):
        return platform.system().lower() == "windows"
    
    def _seperator(self):
        return "\\" if self._isOSWindow() else "/"
    
    def _getDefaultLocalCacheDir(self):
        user_home = os.environ['HOME']
        return f"C:{user_home}\\data" if self._isOSWindow() else f"{user_home}/data"
            
    def _getLocalCacheFilePath(self, namespace):
        file_name = self.appId + "+" + self.cluster + "+" + namespace + ".properties"
        return self._getDefaultLocalCacheDir() + self.config_dir + self._seperator() + self.appId + self._seperator() + file_name
    
    def _transformApolloConfigToProperties(self, namespace_format, config):
        props = Properties()
        if namespace_format != "properties":
            props.setProperty("content", config)
            return props
    
        for (key, value) in config.items():
            props.setProperty(key, value)
        return props
    
    def _transformPropertiesToApolloConfig(self, namespace_format, props):
        if namespace_format != ".properties":
            content = props.getProperty("content")
            return {"content": content}
        config = {}
        for (key, value) in props.items():
            config[key] = value
        return config
    
    def storeLocalCacheFile(self, namespace, namespace_format, content):
        props = self._transformApolloConfigToProperties(namespace_format, content)
        namespace_path = self._getLocalCacheFilePath(namespace)
        namespace_dir = os.path.dirname(namespace_path)
        if not os.path.exists(namespace_dir):
            os.makedirs(namespace_dir)
        with open(namespace_path, 'w', encoding='utf-8', newline='\r\n') as f:
            props.store(f)
            
    def loadFromLocalCacheFile(self, namespace, namespace_format):
        props = Properties()
        props.loadFromFile(self._getLocalCacheFilePath(namespace))
        return self._transformPropertiesToApolloConfig(namespace_format, props)
    
    
class Properties(object):
    '''
    实现读写Properties类
    '''
    def __init__(self):
        self._props = {}
        
    
    def loadFromFile(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf-8', newline='\r\n') as f:
                self.load(f)
        except Exception as e:
            logging.error('loadFromFile error: %s', file_name, e)
        
    def load(self, stream):
        for line in list(stream):
            line = line.strip()
            sp = line.split('=')
            self._props[eval(sp[0]).strip()] = eval(sp[1]).strip()

    def getProperty(self, key):
        return self._props.get(key)

    def setProperty(self, key, value):
        self._props[key] = value

    def items(self):
        return self._props.items()
    
    def storeFile(self, file_name, encoding='utf-8'):
        file_dir = os.path.dirname(file_name)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(file_name, 'w') as f:
            self.store(f)

    def store(self, stream):
        for (k, v) in self._props.items():
            stream.write(repr(k) + "=" + repr(v) + "\n")