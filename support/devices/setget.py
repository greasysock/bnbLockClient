from enum import Enum

class DEVICES(Enum):
    lock = "locks"
class INFO(Enum):
    nodes = "node"

class helper():
    def __init__(self, devicetype, deviceid, setcallback, setbroadcast, publisher):
        self.__devicetype = devicetype
        self.__deviceid = deviceid
        self.__devicetopic = "{}/{}/".format(self.__devicetype.value, self.__deviceid)
        self.__callbacksetter = setcallback
        self.__broadcastsetter = setbroadcast
        self.__publisher = publisher
    def set_callback(self, topic, callback):
        self.__callbacksetter(self.__devicetopic+topic, callback)
    def set_broadcast(self, topic, emitter):
        self.__broadcastsetter(self.__devicetopic+topic, emitter)
    def publish(self, topic, message):
        self.__publisher(self.__devicetopic+topic, message)

class info_helper():
    def __init__(self, info_type, setcallback, setbroadcast, publisher):
        self.__infotype = info_type
        self.__info_topic = "{}/".format(self.__infotype.value)
        self.__callbacksetter = setcallback
        self.__broadcastsetter = setbroadcast
        self.__publisher = publisher
    def set_callback(self, topic, callback):
        self.__callbacksetter(self.__info_topic+topic, callback)
    def set_broadcast(self, topic, emitter):
        self.__broadcastsetter(self.__info_topic+topic, emitter)
    def publish(self, topic, message):
        self.__publisher(self.__info_topic+topic, message)