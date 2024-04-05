from enum import Enum


class ChangeListener:
    def onChange(self, change_event):
        pass

class ConfigChangeEvent(object):
    def __init__(self, changes) -> None:
        self.changes = changes

class ConfigChange(object):
    def __init__(self, namespace, key, old_value, new_value, ChangeType):
        self.namespace = namespace
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.change_type = ChangeType
 

class ChangeType(Enum):
    ADD = 1
    MODIFY = 2
    DELETE = 3