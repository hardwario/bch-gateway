#!/usr/bin/env python3

"""
BigClown gateway between USB and MQTT broker.

Usage:
  bc-gateway [options]

Options:
  -D --debug                   Print debug messages.
  -d DEVICE --device=DEVICE    Path to Base unit's device node (default is /dev/ttyACM0).
  -h HOST --host=HOST          MQTT host to connect to (default is localhost).
  -p PORT --port=PORT          MQTT port to connect to (default is 1883).
  -t TOPIC --base-topic=TOPIC  Base MQTT topic (default is nodes).
  --list                       Show list of available devices
  -v --version                 Print version.
  --help                       Show this message.
"""

import os
import sys
from logging import DEBUG, INFO
import logging as log
import json
import platform

from docopt import docopt
import paho.mqtt.client as mqtt
from serial import Serial
from serial.tools import list_ports

if platform.system() == 'Linux':
    import fcntl

__version__ = '@@VERSION@@'

DEFAULT_MQTT_HOST = 'localhost'
DEFAULT_MQTT_PORT = 1883
DEFAULT_DEVICE = '/dev/ttyACM0'

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'


def mgtt_on_connect(client, userdata, flags, rc):
    log.info('Connected to MQTT broker with (code %s)', rc)

    client.subscribe('node/+/+/+/+/+')


def mgtt_on_message(client, userdata, msg):
    subtopic = msg.topic[5:]
    payload = msg.payload if msg.payload else b'null'
    userdata['serial'].write(b'["' + subtopic.encode('utf-8') + b'",' + payload + b']\n')


def main():
    arguments = docopt(__doc__, version='bc-gateway %s' % __version__)
    opts = {k.lstrip('-').replace('-', '_'): v
            for k, v in arguments.items() if v}

    log.basicConfig(level=DEBUG if opts.get('debug') else INFO, format=LOG_FORMAT)

    if opts.get('list'):
        for p in list_ports.comports():
            print(p)
        return

    serial = Serial(opts.get('device', DEFAULT_DEVICE), timeout=3.0)
    if platform.system() == 'Linux':
        fcntl.flock(serial.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        log.debug("flock %d" % serial.fileno())

    serial.write(b'\n')

    mqttc = mqtt.Client(userdata={'serial': serial})
    mqttc.on_connect = mgtt_on_connect
    mqttc.on_message = mgtt_on_message

    mqttc.connect(opts.get('host', DEFAULT_MQTT_HOST),
                  opts.get('port', DEFAULT_MQTT_PORT),
                  keepalive=10)
    mqttc.loop_start()

    while True:
        line = serial.readline()
        if line:
            log.debug(line)
            try:
                talk = json.loads(line.decode())
                mqttc.publish('node/' + talk[0], json.dumps(talk[1]), qos=1)
            except Exception as e:
                log.error('Received malformed message: %s', line)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.error(e)
        if os.getenv('DEBUG', False):
            raise e
        sys.exit(1)
