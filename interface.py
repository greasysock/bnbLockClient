import sys, argparse, os, random, json, threading, time
import paho.mqtt.client as mqtt
from support import __author__, __version__, __title__, lockdb, hashing_passwords, passwordgen, prompts, zwave

default_lockdb = 'access.db'
mqtt_address = '192.168.1.9'

default_timeout = 35
default_zwave_timeout = 35

ZWAVE_LOCK = 64
ZWAVE_LOCK_TIME = 5

class incomingHandle(threading.Thread):
    def __init__(self, username, password, mqtt_address=mqtt_address):
        threading.Thread.__init__(self)
        self.__client = mqtt.Client("UnregisteredNode")
        self.__username = username
        self.__client.username_pw_set(self.__username, password=password)
        self.__mqtt_address = mqtt_address
        self.connect()
        self.__response = None
        self.__response_call = None
        self.__register_server_status = 0
        self.__connection = -1
    def on_message(self, client, userdata, msg):
        topics = msg.topic.split('/')
        if topics.__len__() == 2:
            if topics[1] == '@status':
                self.__register_server_status = int(msg.payload.decode('ascii'))
        elif topics.__len__() == 3:
            if topics[2] == self.__response_call:
                self.__response = msg.payload
    def on_connect(self, client, userdata, flags, rc ):
        self.__connection = rc
    def get_connection(self):
        return self.__connection
    def set_response_code(self, code):
        self.__client.subscribe("register/{}/{}".format(self.__username, code))
        self.__response_call = code
    def get_registration_server_status(self):
        return self.__register_server_status
    def publish_node(self, noderegistration, response_call):
        self.set_response_code(response_call)
        time.sleep(2)
        self.__client.publish("register/{}".format(self.__username), payload=noderegistration, qos=1)
    def run(self):
        self.__client.loop_forever()
    def response(self):
        return self.__response
    def connect(self):
        self.__client.connect(self.__mqtt_address)
        self.__client.subscribe("register/@status")
        self.__client.on_message = self.on_message
        self.__client.on_connect = self.on_connect
    def quit(self):
        self.__client.disconnect()
        self.__client.loop_stop(force=True)

def node_setup_prompt():
    node_name =             input("  Node Name  (Example: The Gresocks): ")
    node_location_num = int(input("  House number       (Example: 1133): "))
    node_location_st =      input("  Street name (Example: Davis Drive): ")
    node_location_city =    input("  City               (Example: Apex): ")
    node_location_zip =     input("  Zip code          (Example: 27523): ")
    node_return = passwordgen.random_len(9, set = 2)
    node_password = passwordgen.random_len(250)
    return json.dumps({'Type' : 'node',
                       'Return' : node_return,
            'Name' : node_name,
            'Location' : {
                'street' : node_location_st,
                'number' : node_location_num,
                'city' : node_location_city,
                'zip' : node_location_zip
            },
            'Password' : hashing_passwords.make_hash(node_password)}), node_password, node_return

def node_setup():
    print("Login to bnbLock")
    username = prompts.get_username()
    password = prompts.get_password()
    response = incomingHandle(username, password)
    response.start()
    for count in range(default_timeout):
        if response.get_connection() == 0:
            print("**Connected to MQTT Network!")
            break
        print("...")
        time.sleep(1)
    if response.get_connection() != 0:
        print("  \nERROR: Could not connect to MQTT Netowrk!")
        if response.get_connection() == 5:
            print("    REASON: Incorrect Login")
        elif response.get_connection() == 3:
            print("    REASON: Connection Could not be Established")
        response.quit()
        sys.exit(0)
    for count in range(default_timeout):
        if response.get_registration_server_status() == 1:
            print("**Connected to bnbLock Network!")
            break
        print("...")
        time.sleep(1)
    if response.get_registration_server_status() != 1:
        print("\n  ERROR: Could not connect to bnbLock!\n")
        response.quit()
        sys.exit(0)
    print("\nbnbLock Node Details\n-------------------")
    registration_details, node_password, node_return = node_setup_prompt()
    response.publish_node(registration_details, node_return)

    for count in range(default_timeout):
        if response.response() != None:
            print("**Response from bnbLock!")
            break
        print("...")
        time.sleep(1)
    if response.response() == None:
        print("\n  ERROR: No response from bnbLock!\n")
        response.quit()
        sys.exit(0)
    else:
        response.quit()
    account_details = json.loads(response.response().decode('ascii'))
    if account_details['status'] == 'success':
        print("bnbLock Node Added to Network!")
        nodeid = account_details['nodeid']
        accessdb = lockdb.database(default_lockdb)
        dec_reg = json.loads(registration_details)
        accessdb.set_nodeinfo(nodeid=nodeid,
                              nodepassword=node_password,
                              username=username,
                              nodename=dec_reg['Name'])
        accessdb.set_nodelocation(streetnumber=dec_reg['Location']['number'],
                                  street=dec_reg['Location']['street'],
                                  zip=dec_reg['Location']['zip'],
                                  city=dec_reg['Location']['city'])
        print("Node Setup Successfully!")
        accessdb.save()
        accessdb.close()

def device_setup():
    print("Starting ZWave Network!")
    zw = zwave.service()
    zw.start()
    for x in range(default_timeout):
        if zw.get_ready():
            print("Connected to ZWave Network!")
            break
        time.sleep(2)
        print("...")
    if not zw.get_ready():
        print("  ERROR: Could not configure ZWave Network!")
        zw.stop()
        sys.exit(0)
    zwave_locks = list()
    for node in zw.get_nodes():
        if zw.get_node_type(node) == ZWAVE_LOCK:
            zwave_locks.append(node)
    print('\n\nDevice Configuration Wizard\n---------------------------\n')

    print("\n{} ZWave Lock(s) Found\n".format(zwave_locks.__len__()))
    print( "Lock(s):\n")
    event_locks = list()
    for count, lock in enumerate(zwave_locks):
        print("****ZWave Lock #{}***************************".format(count+1))
        print("        NODE: {}".format(lock.node_id))
        print("MANUFACTURER: \'{}\'".format(lock.manufacturer_name))
        print("PRODUCT NAME: \'{}\'".format(lock.product_name))
        print("********************************************\n")
        event_locks.append((count+1, zw.listen_for_events(lock)))
    print("Every door will unlock to begin setup.")
    time.sleep(5)
    for lock in zwave_locks:
        for value in lock.get_doorlocks():
            lock.set_doorlock(lock.get_doorlocks()[value].value_id, False)
    print("To choose the lock for setup, put the lock in the locked position.")
    time.sleep(10)
    door_locked = False
    selected_node = None
    while not door_locked:
        for count, event_lock in event_locks:
            if event_lock.lock_status.state[0] == True:
                print("ZWave Lock #{} Selected!".format(count))
                selected_node = event_lock.node
                door_locked = True
                break
    print("\n")
    print("Enter Lock Details")
    dblock = lockdb.database(default_lockdb)
    lockid = dblock.new_deviceid
    name = prompts.get_name("Lock", set=2)
    location = prompts.get_name("Location", set=2)
    print("\nDevice Details\n--------------")
    print("      ID: {}".format(lockid))
    print("    Name: {}".format(name))
    print("Location: {}".format(location))
    print("    Type: {}\n".format("Lock"))
    if dblock.get_device(selected_node.name) != None:
        print("Device already exists in database. Quitting...")
        zw.stop()
        sys.exit(0)
    else:
        print("Adding device to bnbLock Network!")
        selected_node.name = lockid
        if lockid == selected_node.name:
            dblock.append_device(name=name,location=location,type='lock',deviceid=lockid)
            print("Device added to bnbLock Network Successfully!")
        else:
            print("Failed to add device to bnbLock Network:(")
    zw.stop()
    return -1

def main():
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-s', '--setup', help='Initializes db for daemon.', action='store_true', required=False )
    parser.add_argument('-n', '--new', help='Add new device to network.', action='store_true', required=False)
    parser.add_argument('-r', '--run', help='Runs mqtt network daemon.', action='store_true',
                        required=False)
    args = parser.parse_args()

    if args.setup:
        db_present = lockdb.testdb(default_lockdb)
        if db_present:
            print('LockDB is already present. Delete current DB to create a new one.')
        elif not db_present:
            lockdb.createdb(default_lockdb)
            print('Node Configuration Wizard\n-------------------------\n')
            node_setup()
    if args.new:
        db_present = lockdb.testdb(default_lockdb)
        if db_present:
            device_setup()
        else:
            print("  ERROR: LockDB is not present.")

if __name__ == '__main__':
    main()