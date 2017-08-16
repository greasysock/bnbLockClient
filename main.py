from support import zwave, zwavelisten, lockdb, mqttclient, passwordgen, hashing_passwords
from support.devices import lock, setget, dbconnector
from support.info import devices as info_devices
import time, sys, json
from enum import Enum
from queue import Queue


from support import scheduler
default_lockdb = 'access.db'
mqtt_address = 'auth.bnbwithme.com'
mqtt_port = 8883

default_timeout = 35

ZWAVE_LOCK = 64
ZWAVE_LOCK_TIME = 5

node_registration = 'register/node'
node_registration_status = 'register/@status'

class server_endpoints(Enum):
    nodes_get_registered = 'nodes/{}/get/registered'
    nodes_set_registered = 'nodes/{}/set/registered'

    nodes_get_status = 'nodes/{}/get/status'

class client_endpoints():

    def __init__(self, username, nodeid):
        self.scope = "users/{}/nodes/{}/devices/".format(username, nodeid)
        self.info_scope = "users/{}/nodes/{}/conf/".format(username, nodeid)


node_username = 'jAePl0sASz4DHfJsI8XSp1MAWcAaOBUAg5tsEW6GvZ1S7yC7VLdmRm7GdSadPoZGGsSr7SORe1TxAYUVii1bCLW2vXpU4Ogqpzco'
node_password = '0ADzFznzovDTzWGiOdVLHN0f8luJqHDPOEaL2qKEoCIiTdPCPyv4btcVDz9V509DrSF3s3hA7TwQWQhOwrG5qvZEW0yxEPDtCssa'

def setup_node():
    auth_client = mqtt_network_startup(username_m=node_username, password_m=node_password)
    lockdb.createdb(default_lockdb)
    password = passwordgen.random_len(150)
    hash_password = hashing_passwords.make_hash(password)
    node_return = passwordgen.random_len(9, set=2)
    registration_message = {
        'type' : 'node',
        'return' : node_return,
        'password' : hash_password
    }
    return_address = '{}/{}'.format(node_registration, node_return)
    auth_client.incoming.set_address_store(return_address)
    time.sleep(3)
    auth_client.outgoing.broadcast_message(node_registration, json.dumps(registration_message))

    success = False
    for x in range(default_timeout):
        if auth_client.incoming.get_address_store(return_address) != None:
            return_values = auth_client.incoming.get_address_store(return_address)
            return_value = json.loads(return_values[0].payload.decode('ascii'))
            if return_value['status'] == 'OKAY':
                print("Successfully Pre-Registered to bnbHome Network!")
                success = return_value
                break
        time.sleep(2)
        print("...")
    if not success:
        print("  ERROR: Could not connect pre-register to bnbHome Network!")
        auth_client.stop()
        sys.exit(0)
    if type(success) != type(bool()):
        print('Registration ID: {}'.format(success['nodeid']))
        authdb = lockdb.database(default_lockdb)
        authdb.set_nodeinfo(nodeid=success['nodeid'], nodepassword=password)
        auth_client.stop()
        sys.exit(0)

def mqtt_network_startup(username_m, password_m):
    auth_client = mqttclient.Connect(username_m, password_m, mqtt_address, port=mqtt_port)
    for x in range(default_timeout):
        if auth_client.get_rc() == 0:
            print("Connected to MQTT Network!")
            break
        time.sleep(2)
        print("...")
    if auth_client.get_rc() != 0:
        print("  ERROR: Could not connect to MQTT Network!")
        auth_client.stop()
        sys.exit(0)
    auth_client.incoming.set_address_store(node_registration_status)
    for x in range(default_timeout):
        try:
            if auth_client.incoming.get_address_store(node_registration_status)[0].topic == node_registration_status and \
                            auth_client.incoming.get_address_store(node_registration_status)[0].payload.decode(
                                'ascii') == '1':
                print("Connected to bnbHome Network!")
                break
            time.sleep(2)
            print("...")
        except TypeError:
            time.sleep(2)
            print("...")
    try:
        if auth_client.incoming.get_address_store(node_registration_status)[0].payload.decode('ascii') != '1':
            print("  ERROR: Could not connect to bnbHome Network!")
            auth_client.stop()
            sys.exit(0)
    except AttributeError:
        print("  ERROR: Could not connect to bnbHome Network!")
        auth_client.stop()
        sys.exit(0)
    return auth_client

def listen_for_message(mqtt_c, topic):
    if mqtt_c.incoming.get_address_store(topic) != None:
        return mqtt_c.incoming.get_address_store(topic)
    return None

def shutdown():
    sys.exit(0)

def register_node():
    print('Shutdown Node and register')
    shutdown()
    def status():
        return 1
    bnbhomeclient.outgoing.frequency = 5
    bnbhomeclient.outgoing.set_broadcast(server_endpoints.nodes_get_status.value.format(authdb.node_username), status, server_endpoints.nodes_get_status.value.format(authdb.node_username))

def get_register_details(details):
    registration_details = json.loads(details)
    authdb.set_noderegistration(username=registration_details['username'], nodename=registration_details['nodename'])
    shutdown()



def main_loop():

    endpoints = client_endpoints(authdb.node_parent, authdb.node_username)

    q = Queue()

    schedul = scheduler.mainthread.interface()
    schedul.start()

    def status():
        return 1

    zw = zwave.service()
    zw.start()

    deviceids = authdb.get_deivceids()

    def device_callback(topic, callback):
        scope_len = endpoints.scope.split('/').__len__() + 1
        full_topic = endpoints.scope + topic
        bnbhomeclient.incoming.set_callback(full_topic, callback, ignore=scope_len)

    def device_broadcast(topic, emitter):
        full_topic = endpoints.scope + topic
        bnbhomeclient.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)

    def device_unique_publisher(unique_id):
        bnbhomeclient.outgoing.broadcast_unique(unique_id)

    def device_publisher(topic, message):
        full_topic = endpoints.scope + topic
        bnbhomeclient.outgoing.broadcast_message(full_topic, message)

    def info_callback(topic, callback):
        scope_len = endpoints.info_scope.__len__()
        full_topic = endpoints.info_scope + topic
        bnbhomeclient.incoming.set_callback(full_topic, callback, ignore=scope_len)

    def info_broadcast(topic, emitter):
        full_topic = endpoints.info_scope + topic
        bnbhomeclient.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)

    def info_unique_publisher(unique_id):
        bnbhomeclient.outgoing.broadcast_unique(unique_id)

    def info_publisher(topic, message, qos=1):
        full_topic = endpoints.info_scope + topic
        bnbhomeclient.outgoing.broadcast_message(full_topic, message, qos=qos)

    #DEVICE CONFIGURATION/FIND

    def zwave_startup():
        for x in range(default_timeout):
            if zw.get_ready():
                print("Connected to ZWave Network!")
                break
            time.sleep(2)
            print("...")
        if not zw.get_ready():
            print("  ERROR: Could not configure ZWave Network!")
            zw.stop()
            shutdown()

        zwave_locks = list()
        for node in zw.get_nodes():
            if zw.get_node_type(node) == ZWAVE_LOCK and node.name in deviceids:
                zwave_locks.append(node)
        return zwave_locks
    zwave_locks = zwave_startup()

    # DEVICE INIT

    for lock_z in zwave_locks:
        sg_object = setget.helper(setget.DEVICES.lock, lock_z.name, device_callback, device_broadcast, device_publisher)
        db_connector = dbconnector.con_select(lock_z.name, authdb, dbconnector.datatypes.lock, q)
        lock_listen = zw.listen_for_events(lock_z, trigger=device_unique_publisher)
        lock.device(lock_z.name, lock_z, sg_object, lock_listen, db_connector, schedul)

    # CONF INIT

    info_devices_helper = setget.info_helper(setget.INFO.nodes, info_callback, info_broadcast, info_publisher)
    info_devices.info(info_devices_helper, authdb, q)

    bnbhomeclient.outgoing.frequency = 30
    bnbhomeclient.outgoing.set_broadcast(server_endpoints.nodes_get_status.value.format(authdb.node_username), status, server_endpoints.nodes_get_status.value.format(authdb.node_username))

    while True:
        # now the main thread doesn't care what function it's executing.
        # previously it assumed it was sending the message to display().
        return_queue, f, args, kwargs = q.get()
        results = f(*args, **kwargs)
        return_queue.put(results)
        q.task_done()

if __name__ == "__main__":
    db_present = lockdb.testdb(default_lockdb)
    if not db_present:
        setup_node()
    if db_present:
        authdb = lockdb.database(default_lockdb)
        bnbhomeclient = mqtt_network_startup(authdb.node_username, authdb.node_password)
        bnbhomeclient.incoming.set_address_store(server_endpoints.nodes_set_registered.value.format(authdb.node_username))

        bnbhomeclient.outgoing.broadcast_message(server_endpoints.nodes_get_registered.value.format(authdb.node_username), message=1)
        get_message = listen_for_message(bnbhomeclient, server_endpoints.nodes_set_registered.value.format(authdb.node_username))

        registered = None

        for x in range(default_timeout):
            if get_message != None:
                if get_message[0].payload.decode('ascii') == '0':
                    registered = False
                    break
                registered = json.loads(get_message[0].payload.decode('ascii'))
                if get_message[0].payload.decode('ascii') != 0 or get_message[0].payload.decode('ascii') != -1 or get_message[0].payload.decode('ascii') != None:
                    registered = get_message[0].payload.decode('ascii')
                if registered:
                    break
            bnbhomeclient.outgoing.broadcast_message(server_endpoints.nodes_get_registered.value.format(authdb.node_username), message=1)

            time.sleep(2)
            get_message = get_message = listen_for_message(bnbhomeclient, server_endpoints.nodes_set_registered.value.format(authdb.node_username))

        if registered == None:
            shutdown()

        if authdb.node_parent == '' and authdb.node_name == '' and not registered:
            register_node()
        elif authdb.node_parent == '' and authdb.node_name == '' and registered:
            get_register_details(registered)
        elif authdb.node_parent and authdb.node_name and registered:
            main_loop()
