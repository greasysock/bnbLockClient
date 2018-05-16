from support import zwave, zwavelisten, lockdb, mqttclient, passwordgen, hashing_passwords
from support.devices import lock, setget, dbconnector
from support.devices.control import controller
from support.info import devices as info_devices
import time, sys, json, os
from enum import Enum
from queue import Queue


from support import scheduler, config
default_lockdb = 'access.db'
mqtt_address = 'auth.bnbwithme.com'
mqtt_port = 8883

default_timeout = 35

ZWAVE_LOCK = 64
ZWAVE_LOCK_TIME = 5

node_registration = 'register/node'
node_registration_status = 'register/@status'

#Create Enum for endpoints that are on bnbLockServer
class server_endpoints(Enum):
    nodes_get_registered = 'nodes/{}/get/registered'
    nodes_set_registered = 'nodes/{}/set/registered'

    nodes_get_status = 'nodes/{}/get/status'

#Endpoints for client application
class client_endpoints():

    def __init__(self, username, nodeid):
        self.scope = "users/{}/nodes/{}/devices/".format(username, nodeid)
        self.info_scope = "users/{}/nodes/{}/conf/node/".format(username, nodeid)

#Default user and pass to create a new user on the bnbLock network
node_username = 'jAePl0sASz4DHfJsI8XSp1MAWcAaOBUAg5tsEW6GvZ1S7yC7VLdmRm7GdSadPoZGGsSr7SORe1TxAYUVii1bCLW2vXpU4Ogqpzco'
node_password = '0ADzFznzovDTzWGiOdVLHN0f8luJqHDPOEaL2qKEoCIiTdPCPyv4btcVDz9V509DrSF3s3hA7TwQWQhOwrG5qvZEW0yxEPDtCssa'




def setup_node(conf=None):
    auth_client = mqtt_network_startup(username_m=node_username, password_m=node_password)
    #Creates a new lockdb file
    lockdb.createdb(default_lockdb)
    #Generates a random password
    password = passwordgen.random_len(150)
    #Hashes password
    hash_password = hashing_passwords.make_hash(password)
    #Creates a random id for the bnbLock Server to return a message on.
    node_return = passwordgen.random_len(9, set=2)
    
    #Only sends the hashed password to the node, so the password is never broadcast
    registration_message = {
        'type' : 'node',
        'return' : node_return,
        'password' : hash_password
    }
    """
    Detemerine the address on the MQTT netowrk to listen for the return message from the registration server.
    After we figure out where to listen, we set the MQTT client to listen on that address.
    """
    return_address = '{}/{}'.format(node_registration, node_return)
    auth_client.incoming.set_address_store(return_address)
    time.sleep(3)
    
    #Broadcast registration details to bnbLock Server
    auth_client.outgoing.broadcast_message(node_registration, json.dumps(registration_message))
    success = False
    """
    Start loop to check for reply from bnbLock Server by registering to return_address
    and checking if there are any messages on that address.
    """
    for x in range(default_timeout):
        #Check if message has been received on that return_address
        if auth_client.incoming.get_address_store(return_address) != None:
            #If a message was received, check the status of the registration.
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
    #If sucess was changed from a bool into a dictionary, the registration must have been successful.
    if type(success) != type(bool()):
        print('Registration ID: {}'.format(success['nodeid']))
        authdb = lockdb.database(default_lockdb)
        authdb.set_nodeinfo(nodeid=success['nodeid'], nodepassword=password)
        auth_client.stop()
        sys.exit(0)
        
#This function starts up MQTT client
def mqtt_network_startup(username_m, password_m):
    auth_client = mqttclient.Connect(username_m, password_m, mqtt_address, port=mqtt_port)
    for x in range(default_timeout):
        #Check if good connection was made
        if auth_client.get_rc() == 0:
            print("Connected to MQTT Network!")
            break
        time.sleep(2)
        print("...")
    if auth_client.get_rc() != 0:
        #If a good connection was not made, exit.
        print("  ERROR: Could not connect to MQTT Network!")
        auth_client.stop()
        sys.exit(0)
    #Check if node is registered on bnbHome network.
    auth_client.incoming.set_address_store(node_registration_status)
    for x in range(default_timeout):
        try:
            #Registration server will return 1 if node/client is on network.
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
        #Registration server will return -1 if not on network.
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

#Self explainatory
def shutdown():
    sys.exit(0)

def register_node():
    print('Shutdown Node and register')
    shutdown()
    def status():
        return 1
    bnbhomeclient.outgoing.frequency = 5
    bnbhomeclient.outgoing.set_broadcast(server_endpoints.nodes_get_status.value.format(authdb.node_username), status, server_endpoints.nodes_get_status.value.format(authdb.node_username))

#Function to help with node registration
def get_register_details(details):
    registration_details = json.loads(details)
    authdb.set_noderegistration(username=registration_details['username'], nodename=registration_details['nodename'])
    shutdown()


"""Main looping function
This loop is composed of 4 threads
Thread 0: Main thread that handles the sqlite file
Thread 1: Scheduling thread for events
Thread 2: Incoming thread for MQTT. Listens for events on network and executes them.
Thread 3: ZWave thread that listens to events on zwave network and broadcasts events on mqtt network if necessary.
"""
def main_loop(bnbhomeclient, conf=None):
    #Generate node endpoints on bnbHome network. Nodes only have access to their own endpoints.
    endpoints = client_endpoints(authdb.node_parent, authdb.node_username)
    #Create a queue on main thread for accessing main thread for writing to slite db from other threads.
    q = Queue()
    
    #Start a scheduling thread to schedule tasks to be executed.
    schedul = scheduler.mainthread.interface()
    schedul.start()
    
    def status():
        return 1
    
    #Check if there is any config file on zwave service
    if conf == None:
        zw = zwave.service()
    else:
        zw = zwave.service(device=conf['device_path'])
    zw.start()
    
    #Get the ids of devices already registered on node.
    deviceids = authdb.get_deivceids()

    def device_callback(topic, callback):
        """
        Sets callback for device or service on particular topic
        :param topic: (String) Device or service topic
        :param callback: (Method) Method to callback onto when topic is broadcast on
        :return: None, function is used by device/service controller to create new callbacks.
        """
        scope_len = endpoints.scope.split('/').__len__() + 1
        full_topic = endpoints.scope + topic
        bnbhomeclient.incoming.set_callback(full_topic, callback, ignore=scope_len)

    def device_broadcast(topic, emitter):
        """
        Broadcasts function that returns a value to particular topic.
        Example: Method status() returns 1, and this value is emitted onto topic every 60 seconds.
        :param topic: (String) Device or service topic
        :param emitter: (Method) Method to call when broadcasting
        :return: None, function is used by device/service controller to create new callbacks
        """
        full_topic = endpoints.scope + topic
        bnbhomeclient.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)

    def device_unique_publisher(unique_id):
        """
        Create broadcast triggers that device can use to trigger broadcast after a certain event.
        :param unique_id: Id of device
        :return: None, function is used by device/service controller to create new unique publishing events.
        """
        bnbhomeclient.outgoing.broadcast_unique(unique_id)

    def device_publisher(topic, message):
        """
        Allows device/service to uniquely publish a payload onto a particular scope.
        :param topic: (String)
        :param message: (String)
        :return:
        """
        full_topic = endpoints.scope + topic
        bnbhomeclient.outgoing.broadcast_message(full_topic, message)

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

        #Create list of zwave locks
        zwave_locks = list()
        for node in zw.get_nodes():
            if zw.get_node_type(node) == ZWAVE_LOCK and node.name in deviceids:
                zwave_locks.append(node)
        return zwave_locks
    zwave_locks = zwave_startup()

    # DEVICE INIT
    devices = list()
    device_controllers = list()
    # Lock device configuration. Uses old and new method for endpoint management.
    for lock_z in zwave_locks:
        # Create device controller object and define device scope.
        device_controller = controller.interface(bnbhomeclient, endpoints.scope, controller.DEVICES.lock, lock_z.name)
        # Create set get object to help create set/get endpoints on node scope.
        sg_object = setget.helper(setget.DEVICES.lock, lock_z.name, device_callback, device_broadcast, device_publisher)
        # Create a db connector object to allow device access to database file from other thread
        db_connector = dbconnector.con_select(lock_z.name, authdb, dbconnector.datatypes.lock, q)
        # Create listener object for events on zwave network. Allows device to trigger publishing events.
        lock_listen = zw.listen_for_events(lock_z, trigger=device_unique_publisher)
        devices.append(lock.device(lock_z, sg_object, lock_listen, db_connector, schedul, device_controller))
        device_controllers.append(device_controller)
    # CONF INIT
    # Create info endpoint for configuration and general node info/health
    info_controller = controller.interface(bnbhomeclient, endpoints.info_scope)
    info_devices.info(info_controller, authdb, q, device_controllers)

    bnbhomeclient.outgoing.frequency = 30
    bnbhomeclient.outgoing.set_broadcast(server_endpoints.nodes_get_status.value.format(authdb.node_username), status, server_endpoints.nodes_get_status.value.format(authdb.node_username))

    # Keep node running and keep queue open for writing to db file.
    while True:
        # now the main thread doesn't care what function it's executing.
        # previously it assumed it was sending the message to display().
        return_queue, f, args, kwargs = q.get()
        results = f(*args, **kwargs)
        return_queue.put(results)
        q.task_done()

if __name__ == "__main__":
    """
    Startup method which checks what status node is in.
    There are 4 main states node can be in at any time:
        1. Unregistered, unassigned from user, and no db file present.
        2. Unregistered, unassigned from user, and db file present.
        3. Registered, unassigned from user, and db file present.
        4. Registered, assigned to user, and db file present.
    this method ensures that node is doing the right thing at all times.
    """
    conf = config.conf
    db_present = lockdb.testdb(default_lockdb)
    # If no db is present start new node setup
    if not db_present:
        setup_node()
    # If node db is present startup network to check it's registration status.
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
            get_message = listen_for_message(bnbhomeclient, server_endpoints.nodes_set_registered.value.format(authdb.node_username))

        # Unhandled case
        if registered == None:
            shutdown()

        if authdb.node_parent == '' and authdb.node_name == '' and not registered:
            # Register node onto network
            register_node()
        elif authdb.node_parent == '' and authdb.node_name == '' and registered:
            # If node is already registered to an account, get the registration details
            get_register_details(registered)
        elif authdb.node_parent and authdb.node_name and registered:
            # If registration is intact, run normal loop.
            main_loop(bnbhomeclient,conf=conf)
