#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import click
import click_log
import logging
from bcg.gateway import Gateway
from bcg.utils import *
from bcg.config import load_config

__version__ = '@@VERSION@@'

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
log_level_lut = {'D': 'debug', 'I': 'info', 'W': 'warning', 'E': 'error'}


@click.group(invoke_without_command=True)
@click.option('--config', '-c', 'config_file', type=click.File('r'), help='configuration file (YAML format).')
@click.option('-d', '--device', help='device')
@click.option('-H', '--mqtt-host', help='MQTT host to connect to (default is 127.0.0.1)')
@click.option('-P', '--mqtt-port', help='MQTT port to connect to (default is 1883)')
@click.option('--no-wait', is_flag=True, help='no wait on connect or reconnect serial port')
@click.option('--mqtt-username', help='MQTT username')
@click.option('--mqtt-password', help='MQTT password')
@click.option('--mqtt-cafile', help='MQTT cafile')
@click.option('--mqtt-certfile', help='MQTT certfile')
@click.option('--mqtt-keyfile', help='MQTT keyfile')
@click.option('--retain-node-messages', is_flag=True, help='Set the MQTT retain flag for messages received from nodes')
@click_log.simple_verbosity_option(default='INFO')
@click.option('--debug', '-D', is_flag=True, help='Print debug messages, same as --verbosity DEBUG.')
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, config_file, device, mqtt_host, mqtt_port, no_wait, mqtt_username, mqtt_password, mqtt_cafile, mqtt_certfile, mqtt_keyfile, retain_node_messages, debug):
    '''BigClown gateway between USB serial port and MQTT broker'''

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if ctx.invoked_subcommand:
        return

    config = load_config(config_file)

    if device:
        config['device'] = device

    if mqtt_host:
        config['mqtt']['host'] = mqtt_host

    if mqtt_port:
        config['mqtt']['port'] = mqtt_port

    if mqtt_username:
        config['mqtt']['username'] = mqtt_username

    if mqtt_password:
        config['mqtt']['password'] = mqtt_password

    if mqtt_cafile:
        config['mqtt']['mqtt_cafile'] = mqtt_cafile

    if mqtt_certfile:
        config['mqtt']['certfile'] = mqtt_certfile

    if mqtt_keyfile:
        config['mqtt']['keyfile'] = mqtt_keyfile

    if retain_node_messages:
        config['retain'] = retain_node_messages

    if not config.get('device', None):
        click.echo('The following arguments are required: -d/--device or -c/--config')
        click.echo('Tip: for show available devices use command: bcg devices')
        sys.exit(1)

    try:
        gateway = Gateway(config)
        gateway.start(not no_wait)
    except KeyboardInterrupt as e:
        return


@cli.command('devices')
@click.option('-v', '--verbose', is_flag=True, help='Show more messages')
@click.option('-s', '--include-links', is_flag=True, help='Include entries that are symlinks to real devices')
def command_devices(verbose=False, include_links=False):
    '''Print available devices.'''
    for port, desc, hwid in get_devices(include_links):
        sys.stdout.write("{:20}\n".format(port))
        if verbose:
            sys.stdout.write("    desc: {}\n".format(desc))
            sys.stdout.write("    hwid: {}\n".format(hwid))


@cli.command('help')
@click.argument('command', required=False)
@click.pass_context
def command_help(ctx, command):
    '''Show help.'''
    cmd = cli.get_command(ctx, command)

    if cmd is None:
        cmd = cli

    click.echo(cmd.get_help(ctx))


def main():
    try:
        cli()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)
        if os.environ.get('DEBUG', False):
            raise e
        sys.exit(1)
