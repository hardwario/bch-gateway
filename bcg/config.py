#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
import yaml
from io import IOBase
from schema import Schema, And, Or, Use, Optional, SchemaError

DEFAULT = {
    'mqtt': {
        'host': '127.0.0.1',
        'port': 1883,
    },
    'retain_node_messages': False,
    'qos_node_messages': 1,
    'base_topic_prefix': '',  # ie. 'home-'
    'automatic_remove_kit_from_names': True,
    'automatic_rename_kit_nodes': True,
    'automatic_rename_generic_nodes': True,
    'automatic_rename_nodes': True,
    'rename': {}
}


def port_range(port):
    return 0 <= port <= 65535


schema = Schema({
    Optional('device'): And(str, len),
    Optional('name'): And(str, len),
    Optional('mqtt'): {
        Optional('host'): And(str, len),
        Optional('port'): And(int, port_range),
        Optional('username'): And(str, len),
        Optional('password'): And(str, len),
        Optional('cafile'): And(str, len, os.path.exists),
        Optional('certfile'): And(str, len, os.path.exists),
        Optional('keyfile'): And(str, len, os.path.exists),
    },
    Optional('retain_node_messages'): Use(bool),
    Optional('qos_node_messages'): And(int, lambda qos: 0 <= qos <= 2),
    Optional('base_topic_prefix'): str,  # ie. 'home-'
    Optional('automatic_remove_kit_from_names'): Use(bool),
    Optional('automatic_rename_kit_nodes'): Use(bool),
    Optional('automatic_rename_generic_nodes'): Use(bool),
    Optional('automatic_rename_nodes'): Use(bool),
    Optional('rename'): {}
})


def load_config(config_file):
    if isinstance(config_file, IOBase):
        config = yaml.safe_load(config_file)
        try:
            config = schema.validate(config)
        except SchemaError as e:
            raise Exception('Load Config: ' + str(e))

    elif config_file is None:
        config = {}

    _apply_default(config, DEFAULT)

    return config


def _apply_default(config, default):
    for key in default:
        if key not in config:
            config[key] = default[key]
            continue

        if isinstance(default[key], dict):
            _apply_default(config[key], default[key])


if __name__ == '__main__':
    schema.validate(DEFAULT)
