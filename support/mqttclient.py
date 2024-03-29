"""
mqttclient.py is the send/receive component of the mqtt network.
mqttclient.py is responsible for handling incoming messages and sending those messages off to the correct callbacks
"""

import paho.mqtt.client as mqtt
import json, threading, time
import ssl, sys



tls = {
  'ca_certs':"/etc/ssl/certs/ca-certificates.crt",
  'tls_version':ssl.PROTOCOL_TLSv1_2
}

class FreqException(Exception):
    def __init__(self, message, error):
        super().__init__(message)
        self.error = error
        self.message = message

class Connect():
    def __init__(self, username, password, address, port=1883):
        self.__username = username
        self.__password = password
        self.__address = address
        self.__port = port
        self.__client = mqtt.Client("bnbLock{}".format(username))
        self.__client.username_pw_set(self.__username, self.__password)
        self.__rc = -1
        self.connect()
        self.incoming = self.incoming(self.__client)
        self.incoming.start()
        self.outgoing = self.outgoing(self.__client)
        self.outgoing.start()
    def __on_connect(self, client, userdat, flags, rc):
        self.__rc = rc
    def get_rc(self):
        return self.__rc
    def stop(self):
        self.__client.disconnect()
        sys.exit(0)
    def connect(self):
        self.__client.on_connect = self.__on_connect
        self.__client.tls_set(**tls)
        self.__client.connect(self.__address, self.__port)
    class outgoing(threading.Thread):
        def __init__(self, client):
            threading.Thread.__init__(self)
            self.__client = client
            self.__broadcasts = list()
            self.__unique_broadcasts = dict()
            self.__frequency = 30
        def set_broadcast(self, topic, broadcast_call, unique_id = None):
            new_broadcast = ( topic, broadcast_call )
            broadcast_found = False
            for broadcast in self.__broadcasts:
                if broadcast == new_broadcast:
                    broadcast_found = True
            if broadcast_found:
                return -1
            else:
                self.__broadcasts.append(new_broadcast)
                if unique_id != None:
                    self.__unique_broadcasts[unique_id] = new_broadcast
                    print(self.__unique_broadcasts)
        def set_query_broadcast(self, topic, broadcast_call, unique_id):
            new_broadcast = (topic, broadcast_call)
            self.__unique_broadcasts[unique_id] = new_broadcast
        @property
        def frequency(self):
            return self.__frequency
        @frequency.setter
        def frequency(self, frequency):
            try:
                new_freq = int(frequency)
            except ValueError:
                raise(FreqException("Frequency must be a number", 2))
            if new_freq < 1:
                raise(FreqException("Frequency Too Low", 1))
            self.__frequency = new_freq
        def broadcast_message(self, topic, message, qos=1):
            print(topic)
            print(message)
            self.__client.publish(topic, payload = message, qos=qos)
        def broadcast(self):
            for broadcast in self.__broadcasts:
                self.__client.publish(broadcast[0], payload=broadcast[1](), qos=2)
        def broadcast_unique(self, uniqueid):
            broadcast_details = self.__unique_broadcasts[uniqueid]
            print(broadcast_details)
            self.__client.publish(broadcast_details[0], payload=broadcast_details[1](), qos=2)
        def run(self):
            while True:
                self.broadcast()
                time.sleep(self.__frequency)
                continue
    class incoming(threading.Thread):
        def __init__(self, client):
            threading.Thread.__init__(self)
            self.__client = client
            self.__client.on_message = self.__on_message
            self.__callbacks = list()
            self.__address_stores = dict()
            self.__last_in = (None, None)
        def run(self):
            self.__client.loop_forever()
        def get_last_in(self):
            return self.__last_in
        def __on_message(self, client, userdata, msg):
            print(msg.payload)
            self.__last_in = (userdata, msg)
            address_stores = dict(self.__address_stores)
            for address_store in address_stores:
                if msg.topic == address_store:
                    self.__address_stores[address_store] = (
                        msg,
                        userdata,
                        time.time()
                    )
                    break
            for callback in self.__callbacks:
                if callback[0] == msg.topic:
                    try:
                        topics = msg.topic.split('/')
                        new_topic = "/".join(topics[callback[2]:])
                        new_topic = bytes(new_topic, "utf-8")
                        msg.topic = new_topic
                    except IndexError:
                        None
                    callback[1](client, userdata, msg)
                elif self.__check_wild(callback[0], msg.topic):
                    try:
                        topics = msg.topic.split('/')
                        new_topic = "/".join(topics[callback[2]:])
                        new_topic = bytes(new_topic, "utf-8")
                        msg.topic = new_topic
                    except IndexError:
                        None

                    callback[1](client, userdata, msg)
        def __check_wild(self, callback_topic, topic):
            callback_topics = callback_topic.split('/')
            topics = topic.split('/')
            if callback_topic[-1:] == '+' or callback_topic[-1:] == '#':
                callback_topics_len = callback_topics.__len__() - 1
                if callback_topics[:callback_topics_len] == topics[:callback_topics_len]:
                    return True
                else:
                    return False
            else:
                return False
        def get_address_store(self, topic):
            return self.__address_stores[topic]
        def set_address_store(self, topic):
            found = False
            for s_topic in self.__address_stores:
                if s_topic == topic:
                    found = True
            if not found:
                self.__address_stores[topic] = None
                self.__client.subscribe(topic)

        def set_callback(self, topic, callback, ignore = None):
            if ignore == None:
                new_callback = ( topic, callback )
            else:
                new_callback = ( topic, callback, int(ignore))
            callback_found = False
            for callback in self.__callbacks:
                if callback == new_callback:
                    callback_found = True
            if callback_found:
                return -1
            else:
                self.__client.subscribe(topic)
                self.__callbacks.append(new_callback)
                return 1