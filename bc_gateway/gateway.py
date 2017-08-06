#!/usr/bin/env python3

import os
import sys
import time
import logging
import argparse
import simplejson as json
import platform
import decimal
import yaml
import serial
import serial.tools.list_ports
import paho.mqtt.client

if platform.system() == 'Linux':
    import fcntl

__version__ = '@@VERSION@@'

config = {
    'device': '/dev/ttyACM0',
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': '',
        'password': '',
        'cafile': None,
        'certfile': None,
        'keyfile': None,
    },
    'rename': {}
}

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


class Gateway:

    def __init__(self, config):
        self.ser = serial.Serial(config['device'], timeout=3.0)

        logging.info('Opened serial port: %s', config['device'])

        if platform.system() == 'Linux':
            fcntl.flock(self.ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logging.debug('Exclusive lock on file descriptor: %d' % self.ser.fileno())

        self.ser.write(b'\n')

        self._rename_id = config['rename']
        self._rename_name = {v: k for k, v in config['rename'].items()}
        self._address = None
        self._sub = set(['gateway/ping', 'node/+/+/+/+/+'])

        self.mqttc = paho.mqtt.client.Client()
        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_message = self.mqtt_on_message
        self.mqttc.message_callback_add("gateway/ping", self.gateway_ping)

        self.mqttc.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
        if config['mqtt']['cafile']:
            self.mqttc.tls_set(config['mqtt']['cafile'], config['mqtt']['certfile'], config['mqtt']['keyfile'])

    def run(self):
        self.mqttc.connect(config['mqtt']['host'], int(config['mqtt']['port']), keepalive=10)
        self.mqttc.loop_start()

        self.ser.write(b'\n')

        self.ser.write(b'["$/info/get", null]\n')

        while True:
            try:
                line = self.ser.readline()
            except serial.SerialException:
                ser.close()
                raise
            if line:
                logging.debug(line)

                if line[0] == '!':
                    self.log_message(line)
                    continue

                try:
                    talk = json.loads(line.decode(), parse_float=decimal.Decimal)
                    if len(talk) != 2:
                        raise Exception
                except Exception:
                    logging.error('Invalid JSON message received from serial port: %s', line)

                subtopic = talk[0]
                if subtopic.startswith("$/"):
                    self.sys_message(subtopic, talk[1])
                else:
                    try:
                        i = subtopic.find('/')
                        node_ide = subtopic[:i]
                        node_name = self._rename_id.get(node_ide, None)
                        if node_name:
                            subtopic = node_name + subtopic[i:]

                        self.mqttc.publish("node/" + subtopic, json.dumps(talk[1], use_decimal=True), qos=1)
                    except Exception:
                        logging.error('Failed to publish MQTT message: %s', line)

    def mqtt_on_connect(self, client, userdata, flags, rc):
        logging.info('Connected to MQTT broker with code %s', rc)
        for topic in self._sub:
            logging.debug('Subscribe %s' % topic)
            client.subscribe(topic)

    def mqtt_on_message(self, client, userdata, message):
        if message.topic.startswith("gateway"):
            return

        subtopic = message.topic[5:]
        i = subtopic.find('/')
        node_name = subtopic[:i]
        node_id = self._rename_name.get(node_name, None)
        if node_id:
            subtopic = node_id + subtopic[i:]

        payload = message.payload if message.payload else b'null'
        try:
            json.loads(payload)
        except Exception as e:
            logging.error('parse json ' + str(message.topic) + ' ' + str(message.payload) + ' ' + str(e))

        self.ser.write(b'["' + subtopic.encode('utf-8') + b'",' + payload + b']\n')

    def log_message(self, line):
        pass

    def gateway_ping(self, client, userdata, message):
        if "gateway/ping" == message.topic:
            if self._address:
                client.publish("gateway/pong", json.dumps(self._address))

    def sys_message(self, topic, payload):
        print("on_sys_message", topic, payload)
        if "$/info" == topic:
            self._address = payload['address']
            self.mqttc.subscribe('gateway/%s/rename/set' % self._address)


def main():
    argp = argparse.ArgumentParser(description='BigClown gateway between USB serial port and MQTT broker')
    argp.add_argument('-c', '--config', help='path to configuration file (YAML format)')
    argp.add_argument('-d', '--device', help='path to gateway serial port (default is /dev/ttyACM0)')
    argp.add_argument('-H', '--mqtt-host', help='MQTT host to connect to (default is localhost)')
    argp.add_argument('-P', '--mqtt-port', help='MQTT port to connect to (default is 1883)')
    argp.add_argument('-W', '--wait', help='wait on connect or reconnect', action='store_true')
    argp.add_argument('-l', '--list', help='show list of available devices and exit', action='store_true')
    argp.add_argument('--mqtt-username', help='MQTT username')
    argp.add_argument('--mqtt-password', help='MQTT password')
    argp.add_argument('--mqtt-cafile', help='MQTT cafile')
    argp.add_argument('--mqtt-certfile', help='MQTT certfile')
    argp.add_argument('--mqtt-keyfile', help='MQTT keyfile')
    argp.add_argument('-D', '--debug', help='print debug messages', action='store_true')
    argp.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    args = argp.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format=LOG_FORMAT)

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

    if args.list:
        try:
            for p in serial.tools.list_ports.comports():
                print(p)
            sys.exit(0)
        except Exception:
            logging.error('Failed listing available serial ports')
            sys.exit(1)

    while True:
        try:
            gateway = Gateway(config)
            gateway.run()
        except Exception as e:
            logging.error(e)
            if os.getenv('DEBUG', False):
                raise e
        if args.wait:
            time.sleep(3)
        else:
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
