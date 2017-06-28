import openzwave
from openzwave.node import ZWaveNode, ZWaveNodeDoorLock, ZWaveNodeSecurity
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
import time, sys, os, resource

device = "/dev/ttyAMA0"
options = ZWaveOption(device, config_path="/usr/local/lib/python3.4/dist-packages/python_openzwave/ozw_config")
network = ZWaveNetwork(options, log=None)
time_started = 0


print("------------------------------------------------------------")
print("Waiting for network awaked : ")
print("------------------------------------------------------------")
for i in range(0,300):
    if network.state>=network.STATE_AWAKED:

        print(" done")
        print("Memory use : {} Mo".format( (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)))
        break
    else:
        sys.stdout.write(".")
        sys.stdout.flush()
        time_started += 1
        time.sleep(1.0)
if network.state<network.STATE_AWAKED:
    print(".")
    print("Network is not awake but continue anyway")
print("------------------------------------------------------------")
print("Use openzwave library : {}".format(network.controller.ozw_library_version))
print("Use python library : {}".format(network.controller.python_library_version))
print("Use ZWave library : {}".format(network.controller.library_description))
print("Network home id : {}".format(network.home_id_str))
print("Controller node id : {}".format(network.controller.node.node_id))
print("Controller node version : {}".format(network.controller.node.version))
print("Nodes in network : {}".format(network.nodes_count))
print("------------------------------------------------------------")
print("Waiting for network ready : ")
print("------------------------------------------------------------")
for i in range(0,300):
    if network.state>=network.STATE_READY:
        print(" done in {} seconds".format(time_started))
        break
    else:
        sys.stdout.write(".")
        time_started += 1
        #sys.stdout.write(network.state_str)
        #sys.stdout.write("(")
        #sys.stdout.write(str(network.nodes_count))
        #sys.stdout.write(")")
        #sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(1.0)


print("Memory use : {} Mo".format( (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)))
if not network.is_ready:
    print(".")
    print("Network is not ready but continue anyway")

print("------------------------------------------------------------")
print("Controller capabilities : {}".format(network.controller.capabilities))
print("Controller node capabilities : {}".format(network.controller.node.capabilities))
print("Nodes in network : {}".format(network.nodes_count))
print("Driver statistics : {}".format(network.controller.stats))
print("------------------------------------------------------------")