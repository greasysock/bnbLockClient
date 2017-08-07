from enum import Enum

class DEVICES(Enum):
    LOCKS = 'locks'
class zwavelocks(Enum):
    YALE = 'Yale'
    SCHLAGE = 'Schlage'

class lockstates(Enum):
    LOCAL   = 0 # "unlocked/locked inside"
    REMOTE  = 1 # "unlocked/locked zwave"
    KEYPAD  = 2 # "unlocked/locked from keypad"
    AUTO    = 3 # "unlock/lock from autolock"

methods = {
    DEVICES.LOCKS : {
        "Unknown: type=0004, id=aa00" : zwavelocks.YALE,
        "" : zwavelocks.SCHLAGE
    }
}

def discover_generic(node):
    product_name = node.product_name
    type = None
    for devices in methods:
        for device in methods[devices]:
            if device == product_name:
                type = devices
                break
    return type

def discover_type(node):
    produce_name = node.product_name
    type = None
    for devices in methods:
        for device in methods[devices]:
            if device == produce_name:
                type = methods[devices][device]
                break
    return type

class EventHandle():
    def __init__(self, node, trigger=None):
        self.__trigger = trigger
        self.__node = node
        self.__node_type = discover_generic(node)
        self.__node_method = discover_type(node)

        #Doorlock Events
        self.lock_status = None
        self.lock_codes_status = None

        self.__events = list()
        self.__configure()
    def __configure(self):
        if self.__node_type == DEVICES.LOCKS:
            if self.__node_method == zwavelocks.YALE:
                self.lock_status = YaleLockEvents(self.__trigger, self.__node)
            self.__events.append(self.lock_status)
    def process(self, eventdict):
        for eventtype in self.__events:
            eventtype.process(eventdict)
        return -1

    @property
    def type(self):
        return self.__node_type

    @property
    def node_id(self):
        return self.__node.node_id

    @property
    def node(self):
        return self.__node



class DeviceEvents():
    def __init__(self, broadcast_trigger, node):
        self.trigger = broadcast_trigger
        self.node = node
        self.test = print

class LockEvents(DeviceEvents):
    __status = False
    __lockstate = None
    __user = None
    __battery = -1
    __user_codes = list()
    def __init__(self, broadcast_trigger, node):
        DeviceEvents.__init__(self, broadcast_trigger, node)
        self.__trigger = broadcast_trigger
        self.__node = node
    @property
    def state(self):
        print(self.__status, self.__lockstate, self.__user)
        return self.__status, self.__lockstate, self.__user
    @state.setter
    def state(self, data):
        self.__status = data[0]
        self.__lockstate = data[1]
        self.__user = data[2]
    @property
    def battery_level(self):
        return self.__battery
    @battery_level.setter
    def battery_level(self, value):
        self.__battery = value
    def append_user_code_event(self, event):
        list_cop = list(self.__user_codes)
        for code_event in list_cop:
            if event[0] == code_event[0]:
                self.__user_codes.remove(code_event)
        self.__user_codes.append(event)
    def get_user_code_event(self):
        return self.__user_codes
    def process(self, eventdict):
        return -1
class YaleLockEvents(LockEvents):
    lock_state = {
        19 : (False, lockstates.KEYPAD),
        22 : (False, lockstates.LOCAL),
        25 : (False, lockstates.REMOTE),
        21 : (True, lockstates.LOCAL),
        27 : (True, lockstates.AUTO),
        24 : (True, lockstates.REMOTE)
    }
    __last_message = None
    def process(self, eventdict):
        valueId = eventdict['valueId']
        cc = valueId['commandClass']
        value = str(valueId['value'])
        index = valueId['index']


        if cc == 'COMMAND_CLASS_ALARM' and int(value) in self.lock_state.keys():
            print(cc)
            print(value)
            lockstatus = self.lock_state[int(value)]
            self.state = (lockstatus[0], lockstatus[1], 0)
            self.trigger("locks/{}/get/lockstate".format(self.node.name))
        elif cc == 'COMMAND_CLASS_BATTERY':
            self.battery_level = int(value)
            self.trigger("locks/{}/get/battery".format(self.node.name))
        elif cc == 'COMMAND_CLASS_USER_CODE':
            event = (int(index), value.split('\x00')[0])
            print(event)
            self.append_user_code_event(event)
        if index > 0:
            last_message = eventdict
        return -1