Apyllo - Python Client for Ctrip's Apollo
================

fork自： filamoon/pyapollo

那个老哥好像不维护了，我在这维护一下，正好现在工作是做apollo

新增Feature
* **变更监听**

  ```python
  
    client = ApolloClient('10001')
    
    listener = ChangeListener()
    listener.onChange = lambda event: print(f'onchange: {event.changes}')
    client.add_change_listener(listener)
    client.start()
  
  ```

# Reference
Apollo : https://github.com/ctripcorp/apollo
