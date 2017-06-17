#!/usr/bin/env python3

import os
import sys
import time
import logging
import argparse
import json
import platform
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
        'topic': 'node'
    }
}

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


def mqtt_on_connect(client, userdata, flags, rc):
    logging.info('Connected to MQTT broker with code %s', rc)
    client.subscribe(userdata['base_topic'] + '+/+/+/+/+')


def mqtt_on_message(client, userdata, message):
    subtopic = message.topic[len(userdata['base_topic']):]
    payload = message.payload if msg.payload else b'null'
    userdata['serial'].write(b'["' + subtopic.encode('utf-8') + b'",' + payload + b']\n')


def run():
    base_topic = config['mqtt']['topic'].rstrip('/') + '/'

    ser = serial.Serial(config['device'], timeout=3.0)

    logging.info('Opened serial port: %s', config['device'])

    if platform.system() == 'Linux':
        fcntl.flock(ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.debug('Exclusive lock on file descriptor: %d' % ser.fileno())

    ser.write(b'\n')

    mqttc = paho.mqtt.client.Client(userdata={'serial': ser, 'base_topic': base_topic})
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    mqttc.connect(config['mqtt']['host'], config['mqtt']['port'], keepalive=10)
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
                talk = json.loads(line.decode())
            except Exception:
                logging.error('Invalid JSON message received from serial port: %s', line)
            try:
                mqttc.publish(base_topic + talk[0], json.dumps(talk[1]), qos=1)
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
    argp.add_argument('-D', '--debug', help='print debug messages', action='store_true')
    argp.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    args = argp.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format=LOG_FORMAT)

    if args.config:
        try:
            with open(args.config, 'r') as f:
                config.update(yaml.load(f))
        except Exception:
            logging.error('Failed opening configuration file')
            sys.exit(1)

    config['device'] = args.device if args.device else config['device']
    config['mqtt']['host'] = args.mqtt_host if args.mqtt_host else config['mqtt']['host']
    config['mqtt']['port'] = args.mqtt_port if args.mqtt_port else config['mqtt']['port']
    config['mqtt']['topic'] = args.mqtt_topic if args.mqtt_topic else config['mqtt']['topic']

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
