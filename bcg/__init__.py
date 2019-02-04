#!/usr/bin/env python3
import sys
import os
import argparse
from distutils.version import LooseVersion
import serial.tools.list_ports
import logging
from bcg.gateway import Gateway

__version__ = '@@VERSION@@'

config = {
    'device': None,
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': '',
        'password': '',
        'cafile': None,
        'certfile': None,
        'keyfile': None,
    },
    'base_topic_prefix': '',  # ie. 'bigclown-'
    'name': None,
    'automatic_remove_kit_from_names': True,
    'automatic_rename_generic_nodes': True,
    'automatic_rename_nodes': True,
    'rename': {}
}

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
log_level_lut = {'D': 'debug', 'I': 'info', 'W': 'warning', 'E': 'error'}
pyserial_34 = LooseVersion(serial.VERSION) >= LooseVersion("3.4.0")


def command_devices(verbose=False, include_links=False):
    if os.name == 'nt' or sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports

    if pyserial_34:
        ports = comports(include_links=include_links)
    else:
        ports = comports()

    sorted(ports)

    for port, desc, hwid in ports:
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
    subparsers['devices'].add_argument('-s', '--include-links', action='store_true', help='include entries that are symlinks to real devices' if pyserial_34 else argparse.SUPPRESS)

    argp.add_argument('-c', '--config', help='path to configuration file (YAML format)')
    argp.add_argument('-d', '--device', help='device')
    argp.add_argument('-H', '--mqtt-host', help='MQTT host to connect to (default is localhost)')
    argp.add_argument('-P', '--mqtt-port', help='MQTT port to connect to (default is 1883)')
    argp.add_argument('--no-wait', help='no wait on connect or reconnect serial port', action='store_true')
    argp.add_argument('--mqtt-username', help='MQTT username')
    argp.add_argument('--mqtt-password', help='MQTT password')
    argp.add_argument('--mqtt-cafile', help='MQTT cafile')
    argp.add_argument('--mqtt-certfile', help='MQTT certfile')
    argp.add_argument('--mqtt-keyfile', help='MQTT keyfile')
    argp.add_argument('-D', '--debug', help='print debug messages', action='store_true')
    argp.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    subparser_help = subparser.add_parser('help', help="show help")
    subparser_help.add_argument('what', help=argparse.SUPPRESS, nargs='?', choices=subparsers.keys())

    # TODO: remove in future
    argp.add_argument('-W', '--wait', help=argparse.SUPPRESS, action='store_true')
    args = argp.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format=LOG_FORMAT)

    if args.command == 'help':
        if args.what:
            subparsers[args.what].print_help()
        else:
            argp.print_help()
        sys.exit()

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
            if os.getenv('DEBUG', False):
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

    if not config['device']:
        argp.print_help()
        print('error: the following arguments are required: -d/--device or -c/--config')
        print('tip: for show available devices use command: bcg devices')
        sys.exit(1)

    try:
        gateway = Gateway(config)
        gateway.start(not args.no_wait)
    except KeyboardInterrupt as e:
        return
    except Exception as e:
        logging.error(e)
        if os.getenv('DEBUG', False):
            raise e
        sys.exit(1)
