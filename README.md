Apyllo - Python Client for Ctrip's Apollo
================

fork自： filamoon/pyapollo

那个老哥好像不维护了，我在这维护一下，正好现在工作是做apollo

新增Feature
* **变更监听**

  event的数据结构见 change.py

  ```python
  
    client = ApolloClient('10001')
    
    listener = ChangeListener()
    listener.onChange = lambda event: print(f'onchange: {event.changes}')
    client.add_change_listener(listener)
    client.start()
  
  ```
* **集群能力**

  cluster的数据结构见 cluster.py

  ```python
  
    client = ApolloClient(appId = '10001', config_server_url = "http://localhost:8080")
  
  ```
  config_server_url 需要配置apollo的注册中心的地址，即configservice的地址，因为configservice起来之后注册中心就起来了

* **磁盘本地配置降级**

  逻辑见 local_file.py

  当集群的所有机器都宕机，会触发磁盘降级，读取本地文件

  本地文件是在每次配置读取成功的时候去修改的

* **打包**

  python setup.py install
  会出现
  ```
  Using /opt/anaconda3/lib/python3.11/site-packages
  Searching for charset-normalizer==2.0.4
  Best match: charset-normalizer 2.0.4
  Adding charset-normalizer 2.0.4 to easy-install.pth file
  Installing normalizer script to /opt/anaconda3/bin

  Using /opt/anaconda3/lib/python3.11/site-packages
  Finished processing dependencies for pyapollo==0.0.1.dev1
  ```
  这样就安装成功了，到对应的目录下查看是否有
  然后就可以在别的python文件中import pyapollo了

  如果出现no module named '自定义的module'，import的时候需要加上相对路径

  ```python
  
    from change import ChangeListener, ConfigChange
    from change import *
    from cluster import Cluster

    from local_file import LocalFileRepository
  
  ```
  改成下面这样再试
  ```python
  
    from .change import ChangeListener, ConfigChange
    from .change import *
    from .cluster import Cluster

    from .local_file import LocalFileRepository
  
  ```

# Reference
Apollo : https://github.com/ctripcorp/apollo

+qq交流：1091771980
