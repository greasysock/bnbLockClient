# File was used during testing.

from support import zwave, zwavelisten, lockdb, mqttclient
from support.devices import lock, setget, dbconnector
from support.info import devices as info_devices
import time, sys
from queue import Queue
from support import scheduler
default_lockdb = 'access.db'
mqtt_address = 'auth.bnbwithme.com'
mqtt_port = 8883

default_timeout = 35
default_zwave_timeout = 35

ZWAVE_LOCK = 64
ZWAVE_LOCK_TIME = 5

dblock = lockdb.database(default_lockdb)

mqtt = mqttclient.Connect(dblock.node_username, dblock.node_password, mqtt_address, port=mqtt_port)
device = "locks"
scope = "users/{}/nodes/{}/devices/".format(dblock.node_parent, dblock.node_username)

device_scope = scope+"{}/{}".format(device, "TEST")


print("Starting ZWave Network!")
zw = zwave.service()
zw.start()

deviceids = dblock.get_deivceids()

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

q = Queue()

schedul = scheduler.mainthread.interface()
schedul.start()
def device_callback(topic, callback):
    scope_len = scope.split('/').__len__() + 1
    full_topic = scope + topic
    mqtt.incoming.set_callback(full_topic, callback, ignore=scope_len)
def device_broadcast(topic, emitter):
    full_topic = scope + topic
    mqtt.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)
def device_unique_publisher(unique_id):
    mqtt.outgoing.broadcast_unique(unique_id)
def device_publisher(topic, message):
    full_topic = scope + topic
    mqtt.outgoing.broadcast_message(full_topic, message)
mqtt.outgoing.frequency = 50
for node in zw.get_nodes():

    if zw.get_node_type(node) == ZWAVE_LOCK and node.name in deviceids:
        sg_object = setget.helper(setget.DEVICES.lock,node.name,device_callback, device_broadcast, device_publisher)
        db_connector = dbconnector.con_select(node.name, dblock, dbconnector.datatypes.lock, q)
        lock_listen = zw.listen_for_events(node, trigger=device_unique_publisher)
        zwave_locks.append(lock.device(node.name,node,sg_object, lock_listen, db_connector, schedul))

info_scope = "users/{}/nodes/{}/info/".format(dblock.node_parent,dblock.node_username)
print('helloworld')

def info_callback(topic, callback):
    scope_len = info_scope.__len__()
    full_topic = info_scope+topic
    print(full_topic)
    mqtt.incoming.set_callback(full_topic, callback, ignore=scope_len)
def info_broadcast(topic, emitter):
    full_topic = info_scope + topic
    mqtt.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)
def info_unique_publisher(unique_id):
    mqtt.outgoing.broadcast_unique(unique_id)
def info_publisher(topic, message, qos=1):
    full_topic = info_scope + topic

    mqtt.outgoing.broadcast_message(full_topic, message, qos=qos)

info_devices_helper = setget.info_helper(setget.INFO.nodes,info_callback, info_broadcast,info_publisher)
info_devices_object = info_devices.info(info_devices_helper,dblock, q)
while True:
    # now the main thread doesn't care what function it's executing.
    # previously it assumed it was sending the message to display().
    return_queue, f, args, kwargs = q.get()
    results = f(*args, **kwargs)
    return_queue.put(results)
    q.task_done()