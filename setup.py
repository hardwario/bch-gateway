#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = ['paho-mqtt>=1.0', 'pyserial>=2.6', 'PyYAML>=3.11', 'simplejson>=3.6.0']

setup(
    name='bc-gateway',
    version='@@VERSION@@',
    description='BigClown gateway between USB and MQTT broker.',
    author='BigClownLabs',
    author_email='karel.blavka@bigclown.com',
    url='https://github.com/bigclownlabs/bch-usb-gateway',
    packages=['bc_gateway'],
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    zip_safe=False,
    keywords=['BigClown', 'BigClownLabs', 'gateway'],
    classifiers=[
        'Development Status :: 4 - Beta',
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
    ],
    entry_points='''
        [console_scripts]
        bc-gateway=bc_gateway.gateway:main
    ''',
    long_description="""
BigClown USB Gateway
"""
)