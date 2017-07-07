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
        'topic': 'node',
        'username': '',
        'password': '',
        'cafile': None,
        'certfile': None,
        'keyfile': None,
    },
    'rename': {}
}

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


def mqtt_on_connect(client, userdata, flags, rc):
    logging.info('Connected to MQTT broker with code %s', rc)
    client.subscribe(userdata['base_topic'] + '+/+/+/+/+')


def mqtt_on_message(client, userdata, message):
    subtopic = message.topic[len(userdata['base_topic']):]
    i = subtopic.find('/')
    node_name = subtopic[:i]
    node_id = userdata['rename'].get(node_name, None)
    if node_id:
        subtopic = node_id + subtopic[i:]

    payload = message.payload if message.payload else b'null'
    try:
        json.loads(payload)
    except Exception as e:
        logging.error('parse json ' + str(message.topic) + ' ' + str(message.payload) + ' ' + str(e))

    userdata['serial'].write(b'["' + subtopic.encode('utf-8') + b'",' + payload + b']\n')


def run():
    base_topic = config['mqtt']['topic'].rstrip('/') + '/'

    ser = serial.Serial(config['device'], timeout=3.0)

    logging.info('Opened serial port: %s', config['device'])

    if platform.system() == 'Linux':
        fcntl.flock(ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.debug('Exclusive lock on file descriptor: %d' % ser.fileno())

    ser.write(b'\n')

    rename = {v: k for k, v in config['rename'].items()}

    mqttc = paho.mqtt.client.Client(userdata={'serial': ser, 'base_topic': base_topic, 'rename': rename})
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    mqttc.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
    if config['mqtt']['cafile']:
        mqttc.tls_set(config['mqtt']['cafile'], config['mqtt']['certfile'], config['mqtt']['keyfile'])
    mqttc.connect(config['mqtt']['host'], int(config['mqtt']['port']), keepalive=10)
    mqttc.loop_start()

    while True:
        try:
            line = ser.readline()
        except serial.SerialException:
            ser.close()
            raise
        if line:
            logging.debug(line)
            try:
                talk = json.loads(line.decode(), parse_float=decimal.Decimal)
            except Exception:
                logging.error('Invalid JSON message received from serial port: %s', line)
            try:
                subtopic = talk[0]
                i = subtopic.find('/')
                node_ide = subtopic[:i]
                node_name = config['rename'].get(node_ide, None)
                if node_name:
                    subtopic = node_name + subtopic[i:]

                mqttc.publish(base_topic + subtopic, json.dumps(talk[1], use_decimal=True), qos=1)
            except Exception:
                logging.error('Failed to publish MQTT message: %s', line)


def main():
    argp = argparse.ArgumentParser(description='BigClown gateway between USB serial port and MQTT broker')
    argp.add_argument('-c', '--config', help='path to configuration file (YAML format)')
    argp.add_argument('-d', '--device', help='path to gateway serial port (default is /dev/ttyACM0)')
    argp.add_argument('-H', '--mqtt-host', help='MQTT host to connect to (default is localhost)')
    argp.add_argument('-P', '--mqtt-port', help='MQTT port to connect to (default is 1883)')
    argp.add_argument('-t', '--mqtt-topic', help='base MQTT topic (default is node)')
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
    config['mqtt']['topic'] = args.mqtt_topic if args.mqtt_topic else config['mqtt']['topic']
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
            run()
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
