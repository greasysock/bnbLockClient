from enum import Enum
import json, time, bson, base64, sqlite3
from queue import Queue

class datatypes(Enum):

    #devices
    lock = -1

    #db idx
    typeidx = 1
    dateidx = 2
    dataididx = 3
    dataidx = 4

    #general data
    battery = 0

    #lock data
    lock_curfew = 1
    lock_access_code_temp = 2
    lock_access_code_perm = 3

perm_access_codes = 4

def asciibase64_to_dict(raw_ascii):
    return bson.loads(base64.decodebytes(bytes(raw_ascii, 'ascii')))
def dict_to_asciibase64(raw_dict):
    return base64.encodebytes(bson.dumps(raw_dict)).decode('ascii')

class connection():
    def __init__(self, deviceid, database, queue):
        self.__deviceid = deviceid
        self.__database = database
        self.__queue = queue
    def set_battery_level(self, battery_level):
        return -1

class lockconnection(connection):
    def __init__(self, deviceid, database, queue):
        connection.__init__(self, deviceid, database, queue)
        self.__deviceid = deviceid
        self.__database = database
        self.__queue = queue
    def __wraper(self, function, *args, **kwargs):
        return_queue = Queue()
        self.__queue.put((return_queue, function, args, kwargs))
        results = return_queue.get()
        return results
    def set_autolock(self, state):
        return -1
    def set_curfew(self, state):
        return -1
    def set_curfew_start(self, start):
        return -1
    def set_curfew_end(self, end):
        return -1
    def get_access_codes_temp(self):
        try:
            raw_temporary_codes = self.__database.get_devicedata_idx(self.__deviceid, datatypes.lock_access_code_temp.value)
        except sqlite3.ProgrammingError:
            raw_temporary_codes = self.__wraper(self.__database.get_devicedata_idx, self.__deviceid, datatypes.lock_access_code_temp.value)
        out_list = list()
        for raw_temp in raw_temporary_codes:
            data = asciibase64_to_dict(raw_temp[datatypes.dataidx.value])
            data['dataid'] = raw_temp[datatypes.dataididx.value]
            out_list.append(data)

        return out_list
    def get_access_code_temp(self, dataid):
        temp_access_codes = self.get_access_codes_temp()
        access_code = None
        for temp_code in temp_access_codes:
            if temp_code['dataid'] == dataid:
                access_code = temp_code
                break
        return access_code
    def update_data(self, dataid, data):
        ascii_d = dict_to_asciibase64(data)
        self.__wraper(self.__database.update_devicedata, self.__deviceid,dataid,ascii_d)
    def remove_data(self, dataid):
        self.__wraper(self.__database.remove_devicedata, self.__deviceid, dataid)
    def get_access_codes_perm(self):
        return -1
    def get_access_codes(self):
        return -1
    def set_access_code_temp(self, data):
        bson_obj = dict_to_asciibase64(data)
        data_id = self.__wraper(self.__database.add_devicedata, type=datatypes.lock_access_code_temp.value,
                                deviceid=self.__deviceid, date=int(time.time()), data=bson_obj)
        if self.__wraper(self.__database.check_dataid, data_id):
            return data_id
        else:
            return False
    def check_response_code(self, code):
        return -1
    def get_response_code(self):
        return -1
    def set_access_code_perm(self, data):
        perm_codes = self.__wraper(self.__database.get_devicedata_idx, self.__deviceid, datatypes.lock_access_code_perm.value)
        print(perm_codes)
        if data['index'] != 0:
            deleted_data = -1
            for device_data in perm_codes:
                codeobj = asciibase64_to_dict(device_data[datatypes.dataidx.value])
                print(codeobj)
                if data['index'] == codeobj['index']:
                    self.__wraper(self.__database.remove_devicedata, self.__deviceid, device_data[datatypes.dataididx.value])
                    deleted_data = device_data[datatypes.dataididx.value]
            if not self.__wraper(self.__database.check_dataid, deleted_data):
                bson_obj = dict_to_asciibase64(data)
                data_id = self.__wraper(self.__database.add_devicedata, type=datatypes.lock_access_code_perm.value,
                                        deviceid=self.__deviceid, date=time.time(), data=bson_obj)
                return self.__wraper(self.__database.check_dataid, data_id)
        return False

device_tree = {
    datatypes.lock : lockconnection
}

def con_select(deviceid, database, devicetype, queue):
    return device_tree[devicetype](deviceid, database, queue)