import sqlite3, bson, base64
from support import passwordgen

tables = [("nodeinfo", "'nodeid' name, 'nodepassword' name, 'username' name, 'nodename' name"),
          ("deviceinfo", "'name' name, 'location' name, 'type' name, 'deviceid' name"),
          ("devicedata", "'deviceid' name, 'type' int, 'date' date,'dataid' name ,'data' text")]

def get_tables():
    out_list = list()
    for table, values in tables:
        out_list.append(table)
    return out_list

class database():

    def __init__(self, file_name):
        self.__conn = sqlite3.connect(file_name)
        self.__c = self.__conn.cursor()
    def integrity_check(self):
        valid_db = get_tables()
        test_db = list()
        for table_name in self.__c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            for table in table_name:
                test_db.append(table)
        if sorted(valid_db) == sorted(test_db):
            return True
        else:
            return False
    def save(self):
        self.__conn.commit()
    def close(self):
        self.__conn.close()
    def check_deviceid(self, deviceid):
        found = False
        for device in self.devices:
            if device[3] == deviceid:
                found = True
                break
        return found
    def check_dataid(self, dataid):
        found = False
        devicedata = self.get_devicedata_all()
        for data in devicedata:
            if data[3] == dataid:
                found = True
                break
        return found
    def get_device(self, deviceid):
        for device in self.__c.execute("SELECT * FROM deviceinfo WHERE deviceid = '{}'".format(deviceid)):
            return device
    def append_device(self, **kwargs):
        command = "INSERT INTO deviceinfo values ('{}', '{}', '{}', '{}')".format(
            kwargs['name'],
            kwargs['location'],
            kwargs['type'],
            kwargs['deviceid'])
        self.__c.execute(command)
        self.save()
    @property
    def new_deviceid(self):
        first_id = passwordgen.random_len(3, set=2)
        while self.check_deviceid(first_id):
            first_id = passwordgen.random_len(3, set=2)
        return first_id
    @property
    def devices(self):
        out_list = list()
        for device in self.__c.execute("SELECT * FROM deviceinfo"):
            out_list.append(device)
        return out_list
    def get_devices(self):
        out_list = list()
        for device in self.__c.execute("SELECT * FROM deviceinfo"):
            out_list.append(device)
        return out_list
    @property
    def new_dataid(self):
        first_id = passwordgen.random_len(3, set=2)
        while self.check_dataid(first_id):
            first_id = passwordgen.random_len(3, set=2)
        return first_id
    def add_devicedata(self, **kwargs):
        id = self.new_dataid
        command = "INSERT INTO devicedata VALUES ('{}', '{}', '{}', '{}', '{}')".format(
            kwargs['deviceid'],
            kwargs['type'],
            kwargs['date'],
            id,
            kwargs['data']
        )
        self.__c.execute(command)
        self.save()
        return id
    def update_devicedata(self, deviceid, dataid, data):
        update_command = '''
        UPDATE devicedata
        SET \"data\" = \'{}\'
        WHERE deviceid = \'{}\' AND 
        dataid = \'{}\''''.format(data, deviceid, dataid)
        self.__c.execute(update_command)
        self.save()
        return -1
    def get_devicedata_all(self):
        out_list = list()
        for data in self.__c.execute("SELECT * FROM devicedata"):
            out_list.append(data)
        return out_list
    def get_devicedata(self, deviceid):
        out_list = list()
        for data in self.__c.execute("SELECT * FROM devicedata WHERE deviceid = '{}'".format(deviceid)):
            out_list.append(data)
        return out_list
    def get_devicedata_idx(self, deviceid, value, idx = 1):
        devicedata = self.get_devicedata(deviceid)
        out_list = list()
        for data in devicedata:
            if data[idx] == value:
                out_list.append(data)
        return out_list
    def remove_devicedata(self, deviceid, dataid):
        self.__c.execute("DELETE FROM devicedata WHERE dataid = '{}' AND deviceid = '{}'".format(dataid, deviceid))
        self.save()

    def get_deivceids(self, idx = 3):
        out_list = list()
        for device in self.devices:
            out_list.append(device[idx])
        return out_list
    def set_nodeinfo(self, **kwargs):
        command = "INSERT INTO nodeinfo VALUES ('{}', '{}', '{}', '{}')"
        self.__c.execute(command.format(kwargs['nodeid'],
                                        kwargs['nodepassword'],
                                        '',
                                        ''))
        self.save()
        return -1
    def set_noderegistration(self, **kwargs):
        command = "UPDATE nodeinfo SET username = '{}', nodename = '{}'".format(kwargs['username'], kwargs['nodename'])
        self.__c.execute(command)
        self.save()
    def get_nodeinfo(self):
        nodeinfo = self.__c.execute("SELECT * FROM nodeinfo")
        for nodeinf in nodeinfo:
            return nodeinf
    @property
    def node_username(self):
        return self.get_nodeinfo()[0]
    @property
    def node_password(self):
        return self.get_nodeinfo()[1]
    @property
    def node_parent(self):
        return self.get_nodeinfo()[2]
    @property
    def node_name(self):
        return self.get_nodeinfo()[3]

def testdb(filename):
    testdb = database(filename)
    return testdb.integrity_check()

def createdb(file_name):
    conn = sqlite3.connect(file_name)
    c = conn.cursor()
    for table, values in tables:
        c.execute("CREATE TABLE '{}' ({})".format(table, values))
    conn.commit()
    conn.close()