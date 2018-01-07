from enum import Enum
import json
from json import JSONDecodeError
from support.devices.control import types


class DEVICES(Enum):
    lock = "locks"
class INFO(Enum):
    nodes = "node"
    conf = 'conf'

def response_code_check(response_code):
    return True

class query_callback():
    def __init__(self, unique_pub, trigger, publisher, get_endpoint, default_accept=1):
        self._default_accept = default_accept
        self._trigger = trigger
        self._publisher = publisher
        self._unique_pub = unique_pub
        self._get_endpoint = get_endpoint

    def query(self, client, userdata, message):
        raw_message = message.payload.decode('ascii')
        if message.payload.decode('ascii') == '1':
            self._trigger(self._unique_pub)
        else:
            try:
                expected_key = ['response']
                json_message = json.loads(raw_message)
                if sorted(expected_key) == sorted(json_message.keys()):
                    if response_code_check(json_message['response']):
                        self._publisher('{}/{}'.format(self._unique_pub, json_message['response']), self._get_endpoint())
            except JSONDecodeError:
                pass

class interface():
    def __init__(self, mqtt_client, device_scope, device_type=None, device_id=None):

        self._mqtt = mqtt_client
        if device_type and device_id:
            self._device_type = device_type.value
            self._device_scope = '{}{}/{}/'.format( device_scope, device_type.value, device_id)
        elif device_type == None and device_id != None:
            self._device_scope = '{}{}'.format(device_scope, device_id)
        elif device_type == None and device_id == None:
            self._device_scope = device_scope
        else:
            self._device_scope = device_scope
        self._scope_len = self._device_scope.split('/').__len__() + 1
        self._trigger = self._mqtt.outgoing.broadcast_unique
        self._device_id = device_id
        self._device_controls = list()

    def get_controls(self):
        out_list = list()

        for control in self._device_controls:

            control_object = dict()

            set_endpoint = control.set_endpoint
            get_endpoint = control.get_endpoint
            query_only = control.query_only

            if set_endpoint:
                control_object['set'] = control.network_name
            if get_endpoint:
                control_object['get'] = control.network_name
                control_object['query'] = 'get/{}'.format(control.network_name)
            if control.properties:
                control_object['properties'] = control.properties

            control_object['type'] = control.control_type
            out_list.append(control_object)

        return out_list

    def append_control(self, control_type):
        set_endpoint = control_type.set_endpoint
        get_endpoint = control_type.get_endpoint
        query_only = control_type.query_only
        topic = control_type.network_name

        if set_endpoint:
            self._control_callback('set/{}'.format(topic),set_endpoint)
        if get_endpoint and not query_only:
            self._control_broadcast('get/{}'.format(topic),get_endpoint)
            query_call = query_callback('get/{}'.format(topic), self._trigger, self._control_publish, get_endpoint)
            self._control_callback('set/get/{}'.format(topic), query_call.query)
        elif get_endpoint and query_only:
            self._control_query('get/{}'.format(topic), get_endpoint)
            query_call = query_callback('get/{}'.format(topic), self._trigger, self._control_publish, get_endpoint)
            self._control_callback('set/get/{}'.format(topic), query_call.query)

        self._device_controls.append(control_type)

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_type(self):
        return self._device_type

    def _control_callback(self, topic, callback):
        full_topic = self._device_scope + topic
        self._mqtt.incoming.set_callback(full_topic, callback, ignore=self._scope_len)

    def _control_broadcast(self, topic, emitter):
        full_topic = self._device_scope + topic
        self._mqtt.outgoing.set_broadcast(full_topic, emitter, unique_id=topic)

    def _control_publish(self, topic, message):
        full_topic = self._device_scope + topic
        self._mqtt.outgoing.broadcast_message(full_topic, message)

    def _control_query(self, topic, emitter):
        full_topic = self._device_scope + topic
        self._mqtt.outgoing.set_query_broadcast(full_topic, emitter, topic)
