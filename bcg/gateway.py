#!/usr/bin/env python3

import os
import sys
import time
import logging
import argparse
import simplejson as json
import platform
import socket
import decimal
import yaml
import serial
import serial.tools.list_ports
import paho.mqtt.client

if platform.system() == 'Linux':
    import fcntl

__version__ = '@@VERSION@@'

config = {
    'device': '/dev/ttyUSB0',
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': '',
        'password': '',
        'cafile': None,
        'certfile': None,
        'keyfile': None,
    },
    'name': None,
    'automatic_rename_kit_nodes': True,
    'rename': {}
}

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
log_level_lut = {'D': 'debug', 'I': 'info', 'W': 'warning', 'E': 'error'}


class Gateway:

    def __init__(self, config):
        self._config = config
        self._alias_list = {}
        self._node_rename_id = config['rename'].copy()
        self._node_rename_name = {v: k for k, v in config['rename'].items()}
        self._name = None
        self._info = None
        self._info_id = None
        self._sub = set(['gateway/ping', 'gateway/all/info/get'])
        self._nodes = set([])

        self._ser_error_cnt = 0
        self.ser = None

        self.mqttc = paho.mqtt.client.Client()
        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_message = self.mqtt_on_message
        self.mqttc.on_disconnect = self.mqtt_on_disconnect
        self.mqttc.message_callback_add("gateway/ping", self.gateway_ping)
        self.mqttc.message_callback_add("gateway/all/info/get", self.gateway_all_info_get)

        self.mqttc.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
        if config['mqtt']['cafile']:
            self.mqttc.tls_set(config['mqtt']['cafile'], config['mqtt']['certfile'], config['mqtt']['keyfile'])

        self._rename()

    def _serial_disconnect(self):
        logging.info('Disconnect serial port')

        self._info_id = None
        self._info = None
        self._rename()
        self._alias_list = {}
        for address in list(self._nodes):
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

                line = line.decode()

                if line[0] == '#':
                    self.log_message(line)
                    continue

                try:
                    talk = json.loads(line, parse_float=decimal.Decimal)
                    if len(talk) != 2:
                        raise Exception
                except Exception:
                    logging.error('Invalid JSON message received from serial port: %s', line)
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
                client.subscribe(topic)

    def mqtt_on_disconnect(self, client, userdata, rc):
        logging.info('Disconnect from MQTT broker with code %s', rc)

    def mqtt_on_message(self, client, userdata, message):
        payload = message.payload.decode('utf-8')

        logging.debug('mqtt_on_message %s %s', message.topic, message.payload)

        if message.topic.startswith("gateway"):
            subtopic = message.topic[8 + len(self._name):]
        else:
            subtopic = message.topic[5:]

        if payload == '':
            payload = 'null'

        try:
            payload = json.loads(payload)
        except Exception as e:
            logging.error('parse json ' + str(message.topic) + ' ' + str(message.payload) + ' ' + str(e))
            return

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
        self.mqttc.publish(topic, json.dumps(payload, use_decimal=True), qos=1)

    def log_message(self, line):
        logging.debug('log_message %s', line)
        if self._info_id:
            level_char = line[line.find("<") + 1]
            self.publish(['log', self._info_id, log_level_lut[level_char]], line[1:].strip())

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

        elif topic == "$eeprom/alias/add/ok":
            self._alias_list[payload] = self._node_rename_id[payload]

        elif topic == "$eeprom/alias/remove/ok":
            self._alias_list.pop(payload, None)

    def gateway_message(self, topic, payload):
        if "/info" == topic:
            # TODO: remove in the future
            if 'address' in payload:
                payload['id'] = payload['address']
                del payload['address']

            self._info_id = payload['id']
            self._info = payload
            self._rename()

            # TODO: remove in the future
            if self._info["firmware"].startswith("bcf-usb-gateway"):
                self.node_add(self._info_id)

            if self._info["firmware"].startswith("bcf-gateway-core-module"):
                self.node_add(self._info_id)

            self.write("$eeprom/alias/list", 0)

        elif "/nodes" == topic:
            for i, node in enumerate(payload):
                if not isinstance(node, dict):
                    node = {"id": node}
                    payload[i] = node

                self.node_add(node["id"])

                name = self._node_rename_id.get(node["id"], None)
                if name:
                    node["alias"] = name

        elif "/attach" == topic:
            self.node_add(payload)

        elif "/detach" == topic:
            self.node_remove(payload)

        if self._name:
            self.publish(["gateway", self._name, topic[1:]], payload)

    def node_message(self, subtopic, payload):
        i = subtopic.find('/')
        node_ide = subtopic[:i]

        try:
            node_name = self._node_rename_id.get(node_ide, None)
            if node_name:
                subtopic = node_name + subtopic[i:]

            self.mqttc.publish("node/" + subtopic, json.dumps(payload, use_decimal=True), qos=1)

        except Exception:
            raise
            logging.error('Failed to publish MQTT message: %s, %s', subtopic, payload)

        if self._config['automatic_rename_kit_nodes'] and subtopic[i:] == '/info' and 'firmware' in payload:
            if node_ide not in self._node_rename_id:
                if payload['firmware'].startswith("kit-"):
                    name_base = payload['firmware']
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
            self.mqttc.subscribe(topic)

    def sub_remove(self, topic):
        if isinstance(topic, list):
            topic = '/'.join(topic)
        if topic in self._sub:
            logging.debug('unsubscribe %s', topic)
            self._sub.remove(topic)
            self.mqttc.unsubscribe(topic)

    def node_add(self, address):
        logging.debug('node_add %s', address)
        if address in self._nodes:
            return
        self._nodes.update([address])
        self.sub_add(['node', address, '+/+/+/+'])
        name = self._node_rename_id.get(address, None)
        if name:
            self.sub_add(['node', name, '+/+/+/+'])

    def node_remove(self, address):
        logging.debug('node_remove %s', address)
        if address not in self._nodes:
            logging.debug('address not in self._nodes %s', address)
            return
        self._nodes.remove(address)
        self.sub_remove(['node', address, '+/+/+/+'])

        name = self._node_rename_id.get(address, None)
        if name:
            self.sub_remove(['node', name, '+/+/+/+'])

            if address in self._alias_list and self._alias_list[address] == name:
                self.write('$eeprom/alias/remove', address)

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

        self._node_rename_id[address] = name
        self._node_rename_name[name] = address

        if address in self._nodes:
            self.sub_add(['node', name, '+/+/+/+'])

        if address not in self._alias_list or self._alias_list[address] != name:
            self.write('$eeprom/alias/add', {'id': address, 'name': name})

        # if 'config_file' in self._config:
        #     with open(self._config['config_file'], 'r') as f:
        #         config_yaml = yaml.load(f)
        #         config_yaml['rename'] = self._node_rename_id
        #     with open(self._config['config_file'], 'w') as f:
        #         yaml.safe_dump(config_yaml, f, indent=2, default_flow_style=False)

        return True

    def _rename(self):
        if self._name:
            self.sub_remove(["gateway", self._name, '+/+'])

        self._name = None

        name = self._config['name']

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
            self.sub_add(["gateway", self._name, '+/+'])


def command_devices(verbose=False, include_links=False):
    if os.name == 'nt' or sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports

    for port, desc, hwid in sorted(comports(include_links=include_links)):
        sys.stdout.write("{:20}\n".format(port))
        if verbose:
            sys.stdout.write("    desc: {}\n".format(desc))
            sys.stdout.write("    hwid: {}\n".format(hwid))


def main():
    argp = argparse.ArgumentParser(description='BigClown gateway between USB serial port and MQTT broker')

    subparsers = {}
    subparser = argp.add_subparsers(dest='command', metavar='COMMAND')

    subparsers['devices'] = subparser.add_parser('devices', help="show devices")
    subparsers['devices'].add_argument('-v', '--verbose', action='store_true', help='show more messages')
    subparsers['devices'].add_argument('-s', '--include-links', action='store_true', help='include entries that are symlinks to real devices')

    argp.add_argument('-c', '--config', help='path to configuration file (YAML format)')
    argp.add_argument('-d', '--device', help='path to gateway serial port (default is /dev/ttyACM0)')
    argp.add_argument('-H', '--mqtt-host', help='MQTT host to connect to (default is localhost)')
    argp.add_argument('-P', '--mqtt-port', help='MQTT port to connect to (default is 1883)')
    argp.add_argument('--no-wait', help='no wait on connect or reconnect', action='store_true')
    argp.add_argument('--mqtt-username', help='MQTT username')
    argp.add_argument('--mqtt-password', help='MQTT password')
    argp.add_argument('--mqtt-cafile', help='MQTT cafile')
    argp.add_argument('--mqtt-certfile', help='MQTT certfile')
    argp.add_argument('--mqtt-keyfile', help='MQTT keyfile')
    argp.add_argument('-D', '--debug', help='print debug messages', action='store_true')
    argp.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    # TODO: remove in future
    argp.add_argument('-W', '--wait', help=argparse.SUPPRESS, action='store_true')
    args = argp.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format=LOG_FORMAT)

    if args.command == 'devices':
        command_devices(verbose=args.verbose, include_links=args.include_links)
        return

    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_yaml = yaml.load(f)
                for key in config.keys():
                    if type(config[key]) == dict:
                        config[key].update(config_yaml.get(key, {}))
                    elif key in config_yaml:
                        config[key] = config_yaml[key]
                if not config['mqtt']['certfile']:
                    config['mqtt']['certfile'] = None
                if not config['mqtt']['keyfile']:
                    config['mqtt']['keyfile'] = None

            config['config_file'] = args.config

        except Exception as e:
            logging.error('Failed opening configuration file')
            raise e
            sys.exit(1)

    config['device'] = args.device if args.device else config['device']
    config['mqtt']['host'] = args.mqtt_host if args.mqtt_host else config['mqtt']['host']
    config['mqtt']['port'] = args.mqtt_port if args.mqtt_port else config['mqtt']['port']
    config['mqtt']['username'] = args.mqtt_username if args.mqtt_username else config['mqtt']['username']
    config['mqtt']['password'] = args.mqtt_password if args.mqtt_password else config['mqtt']['password']
    config['mqtt']['cafile'] = args.mqtt_cafile if args.mqtt_cafile else config['mqtt']['cafile']
    config['mqtt']['certfile'] = args.mqtt_certfile if args.mqtt_certfile else config['mqtt']['certfile']
    config['mqtt']['keyfile'] = args.mqtt_keyfile if args.mqtt_keyfile else config['mqtt']['keyfile']

    try:
        gateway = Gateway(config)
        gateway.start(not args.no_wait)
    except KeyboardInterrupt as e:
        return
    except Exception as e:
        logging.error(e)
        if os.getenv('DEBUG', False):
            raise e


if __name__ == '__main__':
    main()
