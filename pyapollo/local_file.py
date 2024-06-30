import platform

class LocalFileRepository(object):
    """
    本地文件配置仓库
    访问降级
    """
    def __init__(self) -> None:
        self.config_dir = "/config-cache"
        self.local_root_dir = ""
        
    def getDefaultLocalCacheDir(self):
        return "C:\\opt\\data" if self.isOSWindow() else "/opt/data"
        
    def isOSWindow(self):
        return platform.system().lower() == "windows"