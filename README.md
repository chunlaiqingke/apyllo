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

# Reference
Apollo : https://github.com/ctripcorp/apollo

+qq交流：1091771980
