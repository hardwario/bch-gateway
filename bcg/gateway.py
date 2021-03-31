#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import logging
import simplejson as json
import platform
import socket
import decimal
import yaml
import serial
import paho.mqtt.client
import appdirs

if platform.system() == 'Linux':
    import fcntl


class Gateway:

    def __init__(self, config):
        self._config = config
        self._alias_list = {}
        self._alias_action = {}

        self._node_rename_id = config['rename'].copy()
        self._node_rename_name = {v: k for k, v in config['rename'].items()}
        self._name = None
        self._data_dir = None
        self._cache_nodes = {}
        self._info = None
        self._info_id = None
        self._sub = set(['gateway/ping', 'gateway/all/info/get'])
        self._nodes = {}

        self._auto_rename_nodes = self._config['automatic_rename_nodes'] or self._config['automatic_rename_kit_nodes'] or self._config['automatic_rename_generic_nodes']

        self._ser_error_cnt = 0
        self.ser = None

        self.mqttc = paho.mqtt.client.Client()
        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_message = self.mqtt_on_message
        self.mqttc.on_disconnect = self.mqtt_on_disconnect
        self.mqttc.message_callback_add(config['base_topic_prefix'] + "gateway/ping", self.gateway_ping)
        self.mqttc.message_callback_add(config['base_topic_prefix'] + "gateway/all/info/get", self.gateway_all_info_get)

        self._msg_retain = config['retain_node_messages']
        self._msg_qos = config['qos_node_messages']

        self.mqttc.username_pw_set(config['mqtt'].get('username'), config['mqtt'].get('password'))
        if config['mqtt'].get('cafile'):
            self.mqttc.tls_set(config['mqtt'].get('cafile'), config['mqtt'].get('certfile'), config['mqtt'].get('keyfile'))

        self._rename()

    def _serial_disconnect(self):
        logging.info('Disconnect serial port')

        self._info_id = None
        self._info = None
        self._rename()
        self._alias_list = {}
        self._alias_action = {}

        for address in self._nodes.keys():
            self.node_remove(address)
        self.gateway_all_info_get()

    def _run(self):
        self.ser = serial.Serial(self._config['device'], baudrate=115200, timeout=3.0)

        logging.info('Opened serial port: %s', self._config['device'])

        self._ser_error_cnt = 0

        if platform.system() == 'Linux':
            fcntl.flock(self.ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logging.debug('Exclusive lock on file descriptor: %d' % self.ser.fileno())

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(b'\n')
        self.write("/info/get", None)

        while True:
            try:
                line = self.ser.readline()
            except serial.SerialException:
                self.ser.close()
                self._serial_disconnect()
                raise
            if line:
                logging.debug("read %s", line)

                if line[0] == 0:
                    i = 1
                    while line[i] == 0 and i < len(line):
                        i += 1
                    line = line[i:]

                line = line.decode()

                if line[0] == '#':
                    self.log_message(line)
                    continue

                try:
                    talk = json.loads(line, parse_float=decimal.Decimal)
                    if len(talk) != 2:
                        raise Exception
                except Exception:
                    logging.warning('Invalid JSON message received from serial port: %s', line)
                    if self._info is None:
                        self.write("/info/get", None)
                    continue

                subtopic = talk[0]
                if subtopic[0] == "$":
                    self.sys_message(subtopic, talk[1])

                elif subtopic[0] == "/":
                    self.gateway_message(subtopic, talk[1])

                else:
                    self.node_message(subtopic, talk[1])

    def start(self, reconect):
        logging.info('Start')

        logging.info('Serial port: %s', self._config['device'])
        logging.info('MQTT broker host: %s, port: %d, use tls: %s',
                     self._config['mqtt']['host'],
                     int(self._config['mqtt']['port']),
                     bool(self._config['mqtt'].get('cafile')))

        self.mqttc.connect_async(self._config['mqtt']['host'], int(self._config['mqtt']['port']), keepalive=10)
        self.mqttc.loop_start()

        while True:
            try:
                self._run()
            except serial.serialutil.SerialException as e:
                if e.errno == 2 and self._ser_error_cnt == 0:
                    logging.error('Could not open port %s' % self._config['device'])
                    self._ser_error_cnt += 1

            except Exception as e:
                logging.error(e)
                if os.getenv('DEBUG', False):
                    raise e

            if not reconect:
                break

            time.sleep(3)

    def mqtt_on_connect(self, client, userdata, flags, rc):
        logging.info('Connected to MQTT broker with code %s', rc)

        lut = {paho.mqtt.client.CONNACK_REFUSED_PROTOCOL_VERSION: 'incorrect protocol version',
               paho.mqtt.client.CONNACK_REFUSED_IDENTIFIER_REJECTED: 'invalid client identifier',
               paho.mqtt.client.CONNACK_REFUSED_SERVER_UNAVAILABLE: 'server unavailable',
               paho.mqtt.client.CONNACK_REFUSED_BAD_USERNAME_PASSWORD: 'bad username or password',
               paho.mqtt.client.CONNACK_REFUSED_NOT_AUTHORIZED: 'not authorised'}

        if rc != paho.mqtt.client.CONNACK_ACCEPTED:
            logging.error('Connection refused from reason: %s', lut.get(rc, 'unknown code'))

        if rc == paho.mqtt.client.CONNACK_ACCEPTED:
            for topic in self._sub:
                logging.debug('subscribe %s', topic)
                client.subscribe(self._config['base_topic_prefix'] + topic)

    def mqtt_on_disconnect(self, client, userdata, rc):
        logging.info('Disconnect from MQTT broker with code %s', rc)

    def mqtt_on_message(self, client, userdata, message):
        payload = message.payload.decode('utf-8')
        topic = message.topic[len(self._config['base_topic_prefix']):]

        logging.debug('mqtt_on_message %s %s', message.topic, message.payload)

        if payload == '':
            payload = 'null'

        try:
            payload = json.loads(payload)
        except Exception as e:
            logging.error('parse json ' + str(message.topic) + ' ' + str(message.payload) + ' ' + str(e))
            return

        if topic.startswith("gateway"):
            subtopic = topic[8 + len(self._name):]
            if subtopic == '/alias/set':
                if "id" in payload and "alias" in payload:
                    self.node_rename(payload["id"], payload["alias"])
                return
            elif subtopic == '/alias/remove':
                if payload:
                    self.node_rename(payload, None)
                return
        else:
            subtopic = topic[5:]

        self.write(subtopic, payload)

    def write(self, topic, payload):
        if not self.ser:
            return

        if isinstance(topic, list):
            topic = '/'.join(topic)

        if topic[0] != '/' or topic[0] == '$':
            i = topic.find('/')
            node_name = topic[:i]
            node_id = self._node_rename_name.get(node_name, None)
            if node_id:
                topic = node_id + topic[i:]
        line = json.dumps([topic, payload], use_decimal=True) + '\n'
        line = line.encode('utf-8')
        logging.debug("write %s", line)
        self.ser.write(line)

    def publish(self, topic, payload):
        if isinstance(topic, list):
            topic = '/'.join(topic)
        self.mqttc.publish(self._config['base_topic_prefix'] + topic, json.dumps(payload, use_decimal=True), qos=1)

    def log_message(self, line):
        logging.debug('log_message %s', line)
        if self._name:
            level_char = line[line.find("<") + 1]
            self.publish(['log', self._name, log_level_lut[level_char]], line[1:].strip())

    def gateway_ping(self, *args):
        if self._name:
            self.publish("gateway/pong", self._name)

    def gateway_all_info_get(self, *args):
        if self._name:
            self.publish(["gateway", self._name, "info"], self._info)

    def sys_message(self, topic, payload):
        # logging.debug("on_sys_message %s %s", topic, payload)
        if topic.startswith("$eeprom/alias/list/"):
            topic, page = topic.rsplit('/', 1)
            self._alias_list.update(payload)
            if len(payload) == 8:
                self.write("$eeprom/alias/list", int(page) + 1)
            else:
                logging.debug("alias_list: %s", self._alias_list)
                for address, name in self._alias_list.items():
                    self.node_rename(address, name)

                self.write("/nodes/get", None)

        if topic == "$eeprom/alias/add/ok":
            if self._alias_action[payload] == 'add':
                del self._alias_action[payload]
                self.publish(["gateway", self._name, "alias/set/ok"], {'id': payload, 'alias': self._alias_list.get(payload, None)})
            self._alias_action_next()

        elif topic == "$eeprom/alias/remove/ok":
            if self._alias_action[payload] == 'remove':
                del self._alias_action[payload]
                self.publish(["gateway", self._name, "alias/remove/ok"], {'id': payload, 'alias': self._alias_list.get(payload, None)})
            self._alias_action_next()

    def gateway_message(self, topic, payload):
        if "/info" == topic:
            # TODO: remove in the future
            if 'address' in payload:
                payload['id'] = payload['address']
                del payload['address']
            if payload['id'] == '000000000000':
                self.write("/info/get", None)
                return
            self._info_id = payload['id']
            self._info = payload
            self._rename()

            if self._info["firmware"].startswith("bcf-gateway-core-module") or self._info["firmware"].startswith("bcf-usb-gateway"):
                self._node_rename_id[self._info_id] = self._name
                self._node_rename_name[self._name] = self._info_id
                self.node_add(self._info_id)

            self.write("$eeprom/alias/list", 0)

        elif "/nodes" == topic:
            for i, node in enumerate(payload):
                if not isinstance(node, dict):
                    node = {"id": node}

                self.node_add(node["id"])

                name = self._node_rename_id.get(node["id"], None)
                if name:
                    node["alias"] = name

                info = self._nodes[node["id"]].get('info')
                if info:
                    node['firmware'] = info.get('firmware')
                    node['version'] = info.get('version')

                payload[i] = node

        elif "/attach" == topic:
            self.node_add(payload)

        elif "/detach" == topic:
            self.node_remove(payload)

        if self._name:
            self.publish(["gateway", self._name, topic[1:]], payload)

    def node_message(self, subtopic, payload):

        node_ide, topic = subtopic.split('/', 1)

        try:
            node_name = self._node_rename_id.get(node_ide, None)
            if node_name:
                subtopic = node_name + '/' + topic

            self.mqttc.publish(self._config['base_topic_prefix'] + "node/" + subtopic, json.dumps(payload, use_decimal=True), qos=self._msg_qos, retain=self._msg_retain)

        except Exception:
            raise
            logging.error('Failed to publish MQTT message: %s, %s', subtopic, payload)

        logging.debug('topic %s', topic)

        if topic == 'info' and 'firmware' in payload:

            self._nodes[node_ide]['info'] = payload

            self._save_nodes_json()

            if self._auto_rename_nodes:
                if node_ide not in self._node_rename_id:
                    name_base = None

                    if self._config['automatic_rename_generic_nodes'] and payload['firmware'].startswith("generic-node"):
                        name_base = 'generic-node'
                    elif self._config['automatic_rename_nodes']:
                        name_base = payload['firmware']

                        if self._config['automatic_remove_kit_from_names'] and name_base.startswith("kit-"):
                            name_base = name_base[4:]

                    if name_base:
                        for i in range(0, 32):
                            name = name_base + ':' + str(i)
                            if name not in self._node_rename_name:
                                self.node_rename(node_ide, name)
                                return

    def sub_add(self, topic):
        if isinstance(topic, list):
            topic = '/'.join(topic)
        if topic not in self._sub:
            logging.debug('subscribe %s', topic)
            self._sub.update([topic])
            self.mqttc.subscribe(self._config['base_topic_prefix'] + topic)

    def sub_remove(self, topic):
        if isinstance(topic, list):
            topic = '/'.join(topic)
        if topic in self._sub:
            logging.debug('unsubscribe %s', topic)
            self._sub.remove(topic)
            self.mqttc.unsubscribe(self._config['base_topic_prefix'] + topic)

    def node_add(self, address):
        if address in self._nodes:
            return
        logging.debug('node_add %s', address)
        self._nodes[address] = {}
        if address in self._cache_nodes:
            info = self._cache_nodes[address].get('info')
            if info:
                self._nodes[address]['info'] = info

        self.sub_add(['node', address, '+/+/+/+'])
        name = self._node_rename_id.get(address, None)
        if name:
            self.sub_add(['node', name, '+/+/+/+'])

    def node_remove(self, address):
        logging.debug('node_remove %s', address)
        if address not in self._nodes:
            logging.debug('address not in self._nodes %s', address)
            return
        del self._nodes[address]
        self.sub_remove(['node', address, '+/+/+/+'])

        name = self._node_rename_id.get(address, None)
        if name:
            self.sub_remove(['node', name, '+/+/+/+'])

            if address in self._alias_list and self._alias_list[address] == name:
                self._alias_remove(address)

            if address not in self._config['rename']:
                self._node_rename_id.pop(address, None)
                if self._node_rename_name[name] == address:
                    self._node_rename_name.pop(name, None)

    def node_rename(self, address, name):
        logging.debug('node_rename %s to %s', address, name)

        if name in self._node_rename_name:
            logging.debug('name is exists %s to %s', address, name)
            return False

        old_name = self._node_rename_id.get(address, None)

        if old_name:
            self.sub_remove(['node', old_name, '+/+/+/+'])
            del self._node_rename_name[old_name]

        if name:
            self._node_rename_id[address] = name
            self._node_rename_name[name] = address

            if address in self._nodes:
                self.sub_add(['node', name, '+/+/+/+'])

            if address not in self._alias_list or self._alias_list[address] != name:
                self._alias_add(address, name)

        else:

            if old_name:
                del self._node_rename_id[address]

            self.sub_add(['node', address, '+/+/+/+'])

            self._alias_remove(address)

        # if 'config_file' in self._config:
        #     with open(self._config['config_file'], 'r') as f:
        #         config_yaml = yaml.load(f)
        #         config_yaml['rename'] = self._node_rename_id
        #     with open(self._config['config_file'], 'w') as f:
        #         yaml.safe_dump(config_yaml, f, indent=2, default_flow_style=False)

        return True

    def _alias_add(self, address, alias):
        if address in self._alias_list and self._alias_list[address] == alias:
            return

        self._alias_list[address] = alias

        self._alias_action[address] = 'add'

        if len(self._alias_action) == 1:
            self.write('$eeprom/alias/add', {'id': address, 'name': alias})

    def _alias_remove(self, address):
        if address not in self._alias_list:
            return

        del self._alias_list[address]

        self._alias_action[address] = 'remove'

        if len(self._alias_action) == 1:
            self.write('$eeprom/alias/remove', address)

    def _alias_action_next(self):
        if not self._alias_action:
            return
        for address in self._alias_action:
            action = self._alias_action[address]
            if action == 'add':
                name = self._alias_list[address]
                self.write('$eeprom/alias/add', {'id': address, 'name': name})
            else:
                self.write('$eeprom/alias/remove', address)
            return

    def _rename(self):
        if self._name:
            self.sub_remove(["gateway", self._name, '+/+'])

        self._name = None
        self._data_dir = None
        self._cache_nodes = {}

        name = self._config.get('name')

        if name:
            if "{ip}" in name:
                ip = None
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                except Exception:
                    return
                name = name.replace("{ip}", ip)

            if "{id}" in name:
                if not self._info_id:
                    return
                name = name.replace("{id}", self._info_id)
        elif name is None and self._info and 'firmware' in self._info:
            name = self._info['firmware'].replace('bcf-gateway-', '', 1)
            name = name.split(':', 1)[0]

        self._name = name

        if name:
            self._data_dir = appdirs.user_data_dir('bcg-' + self._name)

            logging.debug('data_dir=%s', self._data_dir)

            os.makedirs(self._data_dir, exist_ok=True)

            try:
                self._cache_nodes = json.load(open(os.path.join(self._data_dir, 'nodes.json')))
            except Exception as e:
                pass

            self.sub_add(["gateway", self._name, '+/+'])

    def _save_nodes_json(self):
        if not self._data_dir:
            return

        try:
            json.dump(self._nodes, open(os.path.join(self._data_dir, 'nodes.json'), 'w', encoding="utf-8"))
        except Exception as e:
            logging.warning(str(e))
