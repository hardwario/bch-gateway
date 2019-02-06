#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import serial
import click
import platform
from distutils.version import LooseVersion

pyserial_34 = LooseVersion(serial.VERSION) >= LooseVersion("3.4.0")


def get_devices(include_links=False):
    if os.name == 'nt' or sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports

    if pyserial_34:
        ports = comports(include_links=include_links)
    else:
        ports = comports()

    return sorted(ports)
