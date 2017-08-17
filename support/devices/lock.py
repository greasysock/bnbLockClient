from support.devices.settype import type
import json, time
from support import passwordgen

#testing
#from support.devices import dbconnector as testdb

DEFAULT_CHANGE_TIMEOUT = 4

class device():
    def __init__(self, deviceid, zwavenode, setget, lockevent, dbconnector, scheduler):
        print('helloworld')
        self.__scheduler = scheduler
        self.__lockevent = lockevent
        self.__deviceid = deviceid
        self.__zw = zwavenode
        self.__setget = setget
        self.__batterylevel = None
        self.__db = dbconnector
        self.__set_get_conf = {
            type.broadcast :
                [ ( self.get_lockstate, "get/lockstate" ),
                  ( self.get_battery, "get/battery")],
            type.callback  :
                [ ( self.set_lockstate,             "set/lockstate" ),

                  ( self.set_access_code,           "set/access_code/+" ),

                  ( self.set_autolock,              "set/autolock"),
                  ( self.set_autolock_curfew,       "set/autolock/#"),

                  ( self.set_get_response_code,     "set/get/response_code")]
        }
        self.__configure_set_get()
        self.__configure_schedule()
    def get_lockstate(self):
        if self.__lockevent.lock_status.state[0]:
            return 1
        else:
            return 0
    def get_battery(self):
        current_level = self.__lockevent.lock_status.battery_level
        return self.__lockevent.lock_status.battery_level
    def set_lockstate(self, client, userdata, msg):
        raw_message = msg.payload.decode('ascii')
        if raw_message == '1':
            for value in self.__zw.get_doorlocks():
                self.__zw.set_doorlock(self.__zw.get_doorlocks()[value].value_id, True)
        elif raw_message == '0':
            for value in self.__zw.get_doorlocks():
                self.__zw.set_doorlock(self.__zw.get_doorlocks()[value].value_id, False)
    def set_autolock(self, client, userdata, msg):
        raw_message = msg.payload.decode('ascii')
        if raw_message == '1':
            self.__db.set_autolock(True)
        elif raw_message == '0':
            self.__db.set_autolock(False)
    def set_autolock_curfew(self, client, userdata, msg):
        topics = msg.topic
        raw_message = msg.payload.decode('ascii')
        topiclen = topics.__len__()
        if topics[2] == 'curfew':
            if topiclen == 3:
                if raw_message == '1':
                    self.__db.set_curfew(True)
                elif raw_message == '0':
                    self.__db.set_curfew(False)
            elif topiclen == 4:
                raw_message = int(raw_message)
                if 0 <= raw_message <= 23:
                    if topics[3] == 'start':
                        self.__db.set_curfew_start(raw_message)
                    elif topics[3] == 'end':
                        self.__db.set_curfew_end(raw_message)
    def set_access_code(self, client, userdata, msg):
        """
         
        :param msg: Expects a json structured like: {
            code : 123456 - empty code will generate random code,
            index : 0 (1-4, 0 takes first available spot or overwrites oldest code)
        }  
        """
        raw_message = msg.payload.decode('ascii')
        try:
            json_message = json.loads(raw_message)
        except ValueError:
            json_message = -1
        topics = msg.topic.split('/')
        topicslen = topics.__len__()
        if topicslen == 3 and json_message != -1:
            if topics[2] == 'perm':
                self.set_access_code_perm(json_message)
            elif topics[2] == 'temp':
                self.set_access_code_temp(json_message)
    def set_get_response_code(self, client, userdata, msg):
        raw_message = msg.payload.decode('ascii')
        try:
            json_message = json.loads(raw_message)
        except ValueError:
            return
        expected_key = ['response']
        if sorted(expected_key) == sorted(json_message.keys()):
            print("here")
            if self.set_get_response_code_check_return(json_message['response']):
                print('here')
                response = self.__db.get_response_code()
                self.__setget.publish('set/get/response_code/{}'.format(json_message['response']), response)

        print(msg.payload)
        print('reponse gen')
    def set_get_response_code_check_return(self, code):
        return True
    def set_access_code_temp(self, data):
        expected_keys = ['start',
                         'end',
                         'response',
                         'length']
        if sorted(expected_keys) == sorted(data.keys()):
            length = int(data['length'])
            if 4 <= length <= 10:
                lencheck = True
            else:
                lencheck = False
            responsecheck = self.__response_check(data['response'])
            startcheck, endcheck = self.__start_end_check(data['start'], data['end'])
            if lencheck and startcheck and endcheck and responsecheck:
                data['stage'] = 0
                dataid = self.__db.set_access_code_temp(data)
                if dataid:
                    access_code = self.__db.get_access_code_temp(dataid)
                    self.__access_code_temp_stage_0_schedule_prep(access_code)
    def set_access_code_perm(self, data):
        expected_keys = ['index',
                         'response',
                         'code']
        if sorted(expected_keys) == sorted(data.keys()):
            index = int(data['index'])
            code = int(data['code'])
            if 0 <= index <= 4:
                indexcheck = True
                print(index)
            else:
                indexcheck = False
            if 4 <= str(code).__len__() <= 10:
                codecheck = True
            else:
                codecheck = False
            responsecheck = self.__response_check(data['response'])
            if indexcheck and codecheck and responsecheck:
                status = self.__db.set_access_code_perm(data)
                if status and data['index'] != 0:
                    self.__zw.set_usercode_at_index(int(data['index']), data['code'])
                    print(self.__zw.get_usercode(int(data['index'])))
    def __response_check(self, response):
        return True
    def __start_end_check(self, start, end):
        start = True
        end = True
        return start, end
    def __configure_set_get(self):
        for broadcast in self.__set_get_conf[type.broadcast]:
            self.__setget.set_broadcast(broadcast[1], broadcast[0])
        for callback in self.__set_get_conf[type.callback]:
            print(callback)
            self.__setget.set_callback(callback[1], callback[0])
    def __configure_schedule(self):
        temp_access_codes = self.__db.get_access_codes_temp()
        for temp_code in temp_access_codes:
            print(temp_code)
            if temp_code['stage'] == 0:
                self.__access_code_temp_stage_0_schedule_prep(temp_code)
            elif temp_code['stage'] == 1:
                self.__access_code_temp_stage_1_schedule_prep(temp_code)
            elif temp_code['stage'] == 2:
                self.__access_code_temp_stage_2_schedule_prep(temp_code)
        return -1
    def __access_code_temp_stage_0_schedule_prep(self, access_code):
        start = int(access_code['start']) - (60*60*24*7) # 7 Days from start
        self.__scheduler.append_task(start, self.access_code_temp_0_to_1, args=(access_code['dataid'],))
        #Start 7 days from start.
        #Function should create access code
        #After access code is created
        #Stage should raise to 1
    def access_code_temp_0_to_1(self, dataid):
        temp_access_codes = self.__db.get_access_codes_temp()
        access_code = None
        for temp_code in temp_access_codes:
            if temp_code['dataid'] == dataid:
                access_code = temp_code
                break
        potential_code = passwordgen.random_len(int(access_code['length']), set=4)
        match = True
        while match:
            found_match = 0
            for temp_code in temp_access_codes:
                if temp_code['stage'] == 1 or temp_code['stage'] == 2:
                    if temp_code['code'] == potential_code:
                        found_match +=1
            if found_match == 0:
                break
            else:
                potential_code = passwordgen.random_len(int(access_code['length']), set=4)
        access_code['code'] = potential_code
        access_code['stage'] = 1
        print(access_code)
        self.__db.update_data(dataid, access_code)
        temp_access_codes = self.__db.get_access_codes_temp()
        for temp_code in temp_access_codes:
            if temp_code['dataid'] == dataid:
                try:
                    if temp_code['code'] == potential_code:
                        self.__access_code_temp_stage_1_schedule_prep(temp_code)
                        print(temp_code)
                        return True
                except KeyError:
                    return False
        return False
    def __access_code_temp_stage_1_schedule_prep(self, access_code):
        #Start at start
        #Function should pick an index to be on
        #and should program the access code on that index
        #After access code is programmed, raise to stage 2
        start = int(access_code['start'])
        self.__scheduler.append_task(start, self.access_code_temp_1_to_2, args=(access_code['dataid'],))

        return -1
    def access_code_temp_1_to_2(self, dataid):
        access_code = self.__db.get_access_code_temp(dataid)
        temp_access_codes = self.__db.get_access_codes_temp()
        last_idx = -1
        potential_idx = 5
        while True:
            mod = False
            for temp_code in temp_access_codes:
                if temp_code['stage'] == 2:
                    if temp_code['index'] == potential_idx:
                        potential_idx +=1
                        mod = True
            if not mod:
                break
        if potential_idx == 17:
            return False
        elif potential_idx <= 16:
            values = self.__zw.get_values(class_id=0x63, type='Raw')
            for value in values:
                if values[value].index == potential_idx:
                    values[value].data = chr(0x01) + access_code['code']
                    values[value].refresh()
                    found = False
                    for x in range(DEFAULT_CHANGE_TIMEOUT):
                        code_events = self.__lockevent.lock_status.get_user_code_event()
                        print(code_events)
                        for code in code_events:
                            if code[0] == potential_idx and code[1] == access_code['code']:
                                found = True
                                break
                            if found: break
                        time.sleep(1)
                    if found:
                        access_code['index'] = potential_idx
                        access_code['stage'] = 2
                        self.__db.update_data(dataid, access_code)
                        self.__access_code_temp_stage_2_schedule_prep(access_code)
                    return found
            return False
    def __access_code_temp_stage_2_schedule_prep(self, access_code):
        #Start at end
        #Function should remove access code from lock
        #After access is removed, remove entry from database
        start = int(access_code['end'])
        self.__scheduler.append_task(start, self.access_code_temp_2_to_null, args=(access_code['dataid'],))

    def access_code_temp_2_to_null(self, dataid):
        access_code = self.__db.get_access_code_temp(dataid)
        access_code_length = access_code['code'].__len__()
        values = self.__zw.get_values(class_id=0x63)
        for value in values:
            if values[value].index == access_code['index']:
                values[value].data = chr(0) * (1+access_code_length)
                values[value].refresh()
                found = False
                for x in range(DEFAULT_CHANGE_TIMEOUT):
                    code_events = self.__lockevent.lock_status.get_user_code_event()
                    print(code_events)
                    for code in code_events:
                        if code[0] == access_code['index'] and code[1] != access_code['code']:
                            found = True
                            break
                    if found: break
                    time.sleep(1)

                if found:
                    self.__db.remove_data(dataid)
                    return True
        return False