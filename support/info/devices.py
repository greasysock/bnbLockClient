from queue import Queue
from support.devices.settype import type
import json

class info():
    def __init__(self, setget, dbconnector, queue):
        self.__setget = setget
        self.__dbconnector = dbconnector
        self.__queue = queue
        self.__set_get_conf = {

            type.callback : [( self.set_get_devices, 'set/get/devices')],
            type.broadcast : []

        }
        self.__configure_set_get()
    def __wraper(self, function, *args, **kwargs):
        return_queue = Queue()
        self.__queue.put((return_queue, function, args, kwargs))
        results = return_queue.get()
        return results
    def set_get_devices(self, client, userdata, msg):
        message = msg.payload.decode('ascii')
        print(message)
        if message == '1':
            devices = self.__wraper(self.__dbconnector.get_devices)
            out_dict = dict()
            out_dict['locks'] = list()
            for device in devices:
                if device[2] == 'lock':
                    out_dict['locks'].append({
                        'id' : device[3],
                        'name' : device[0],
                        'location' : device[1]
                    })
            out_json = json.dumps(out_dict)
            self.__setget.publish('get/devices', out_json)
    def __configure_set_get(self):
        for broadcast in self.__set_get_conf[type.broadcast]:
            self.__setget.set_broadcast(broadcast[1], broadcast[0])
        for callback in self.__set_get_conf[type.callback]:
            self.__setget.set_callback(callback[1], callback[0])
