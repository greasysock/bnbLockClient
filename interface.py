# Interface which adds new locks to bnbHome network from zwave network.

import sys, argparse, os, random, json, threading, time
import paho.mqtt.client as mqtt
from support import __author__, __version__, __title__, lockdb, hashing_passwords, passwordgen, prompts, zwave, config

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



def device_setup(conf=None):
    print("Starting ZWave Network!")
    if conf == None:
        zw = zwave.service()
    else:
        zw = zwave.service(device=conf['device_path'])
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
    if args.new:
        db_present = lockdb.testdb(default_lockdb)
        if db_present:
            device_setup(conf=config.conf)
        else:
            print("  ERROR: LockDB is not present.")

if __name__ == '__main__':
    main()