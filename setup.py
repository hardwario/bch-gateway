#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = ['paho-mqtt>=1.0', 'pyserial>=3.0', 'PyYAML>=3.11', 'simplejson>=3.6.0']

setup(
    name='bcg',
    version='@@VERSION@@',
    description='BigClown USB Gateway',
    author='HARDWARIO s.r.o.',
    author_email='karel.blavka@bigclown.com',
    url='https://github.com/bigclownlabs/bch-usb-gateway',
    packages=['bcg'],
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    zip_safe=False,
    keywords=['BigClown', 'BigClownLabs', 'gateway', 'MQTT'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Environment :: Console'
    ],
    entry_points='''
        [console_scripts]
        bcg=bcg.gateway:main
    ''',
    long_description="""
BigClown gateway between USB and MQTT broker.

Documentation is here https://www.bigclown.com/doc/tools/bcg/


usage: bcg [-h] [-c CONFIG] [-d DEVICE] [-H MQTT_HOST] [-P MQTT_PORT]
           [--no-wait] [--mqtt-username MQTT_USERNAME]
           [--mqtt-password MQTT_PASSWORD] [--mqtt-cafile MQTT_CAFILE]
           [--mqtt-certfile MQTT_CERTFILE] [--mqtt-keyfile MQTT_KEYFILE] [-D]
           [-v]
           COMMAND ...

BigClown gateway between USB serial port and MQTT broker

positional arguments:
  COMMAND
    devices             show devices
    help                show help

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to configuration file (YAML format)
  -d DEVICE, --device DEVICE
                        device
  -H MQTT_HOST, --mqtt-host MQTT_HOST
                        MQTT host to connect to (default is localhost)
  -P MQTT_PORT, --mqtt-port MQTT_PORT
                        MQTT port to connect to (default is 1883)
  --no-wait             no wait on connect or reconnect serial port
  --mqtt-username MQTT_USERNAME
                        MQTT username
  --mqtt-password MQTT_PASSWORD
                        MQTT password
  --mqtt-cafile MQTT_CAFILE
                        MQTT cafile
  --mqtt-certfile MQTT_CERTFILE
                        MQTT certfile
  --mqtt-keyfile MQTT_KEYFILE
                        MQTT keyfile
  -D, --debug           print debug messages
  -v, --version         show program's version number and exit

"""
)
