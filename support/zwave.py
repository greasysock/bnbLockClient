import openzwave
from openzwave.node import ZWaveNode, ZWaveNodeDoorLock, ZWaveNodeSecurity
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from support import zwavelisten
import time, sys, os, resource, threading, enum

class bnbZWaveNetwork(ZWaveNetwork):
    def __init__(self, options, log=None, autostart=False, kvals=True):
        ZWaveNetwork.__init__(self, options, log=log, autostart=autostart,kvals=kvals)
    def _handle_value(self, node=None, value=None):
        return node, value
    def _handle_value_changed(self, args):
        self.handle_value_changed(args)
    def handle_value_changed(self, args):
        return args
class service(threading.Thread):
    def __init__(self, device="/dev/ttyAMA0", config_path="/usr/local/etc/openzwave"):
        threading.Thread.__init__(self)
        self.__device = device
        self.__config_path = config_path
        self.__options = ZWaveOption(device, config_path=self.__config_path)
        self.__options.set_console_output(False)
        self.__options.lock()
        self.__network = None
        self.__network_ready = False
        self.__event_listen = None
    def start_z(self):
        self.__loop_control = True
        self.__start()
        while self.__loop_control:
            continue
    def run(self):
        self.start_z()
    def __start(self):
        self.__network = bnbZWaveNetwork(self.__options, log=None, autostart=False)
        time_started = 0
        self.__network.start()
        for i in range(0, 300):
            if self.__network.state >= self.__network.STATE_AWAKED:
                break
            else:
                time_started += 1
                time.sleep(1.0)
        for i in range(0, 300):
            if self.__network.state >= self.__network.STATE_READY:
                self.__network_ready = True
                print(" done in {} seconds".format(time_started))
                self.__network.handle_value_changed = self.on_value_change
                break
            else:
                time_started += 1
                time.sleep(1.0)

        print("Memory use : {} Mo".format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)))
        if not self.__network.is_ready:
            print(".")
            print("Network is not ready but continue anyway")
    def get_ready(self):
        return self.__network_ready
    def stop(self):
        self.__network.stop()
        self.__loop_control = False
    def get_locks(self):
        out_list = list()
        for node in self.__network.nodes:
            for val in self.__network.nodes[node].get_doorlocks():
                out_list.append(self.__network.nodes[node])
        return out_list
    def get_nodes(self):
        out_list = list()
        for node in self.__network.nodes:
            out_list.append(self.__network.nodes[node])
        return out_list
    def get_node_name(self, node):
        return node.name
    def set_node_name(self, node, name):
        node.name = name
        if node.name == name: return True
        else: return False
    def get_node_type(self, node):
        return node.generic
    def get_lock(self, node):
        return self.__network.nodes[node]
    def set_usercode_at_idx(self, node, idx, code):
        lock_node = self.get_lock(node)
        lock_node.set_usercode_at_index(idx, code)
    def listen_for_events(self, node, trigger=None):
        event_object = zwavelisten.EventHandle(node, trigger)
        try:
            self.__event_listen[node.node_id] = event_object
        except:
            self.__event_listen = dict()
            self.__event_listen[node.node_id] = event_object
        return event_object
    def on_value_change(self, args):
        valueId = args['valueId']
        label = valueId['label']
        value = valueId['value']
        v_id = valueId['id']
        index = valueId['index']
        cc = valueId['commandClass']
        print("{}: {} - {} - ID: {} - IDX: {}".format(label, value, cc, v_id, index))
        if self.__event_listen != None:
            self.__event_listen[int(args['nodeId'])].process(args)