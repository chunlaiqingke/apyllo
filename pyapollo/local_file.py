import platform
from jproperties import Properties

class LocalFileRepository(object):
    """
    本地文件配置仓库
    访问降级
    """
    def __init__(self, appId, cluster) -> None:
        self.config_dir = "/config-cache"
        self.local_root_dir = ""
        self.appId = appId
        self.cluster = cluster
        
    def _isOSWindow(self):
        return platform.system().lower() == "windows"
    
    def _seperator(self):
        return "\\" if self._isOSWindow() else "/"
    
    def _getDefaultLocalCacheDir(self):
        return "C:\\opt\\data" if self._isOSWindow() else "/opt/data"
            
    def _getLocalCacheFilePath(self, namespace):
        file_name = self.appId + "+" + self.cluster + "+" + namespace + ".properties"
        return self._getDefaultLocalCacheDir() + self._seperator() + self.config_dir + self._seperator() + self.appId + self._seperator() + file_name
    
    def _transformApolloConfigToProperties(self, namespace_format, config):
        props = Properties()
        if namespace_format != "properties":
            props.setProperty("content", config)
            return props
    
        for (key, value) in config.items():
            props.setProperty(key, value)
        return props
    
    def _transformPropertiesToApolloConfig(self, namespace_format, props):
        if namespace_format != "properties":
            return props.getProperty("content")
        config = {}
        for (key, value) in props.items():
            config[key] = value
        return config
    
    def persistLocalCacheFile(self, namespace, namespace_format, content):
        props = self._transformApolloConfigToProperties(namespace_format, content)
        with open(self._getLocalCacheFilePath(namespace), 'wb') as f:
            props.store(f, encoding='utf-8')
            
    def loadFromLocalCacheFile(self, namespace, namespace_format):
        props = Properties()
        with open(self._getLocalCacheFilePath(namespace), 'rb') as f:
            props.load(f, 'utf-8')
        return self._transformPropertiesToApolloConfig(namespace_format, props)