#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    requirements = f.read()

setup(
    name='bcg',
    version='@@VERSION@@',
    description='BigClown USB Gateway',
    author='HARDWARIO s.r.o.',
    author_email='karel.blavka@bigclown.com',
    url='https://github.com/bigclownlabs/bch-usb-gateway',
    packages=find_packages(),
    license='MIT',
    keywords=['BigClown', 'BigClownLabs', 'gateway', 'MQTT'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
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
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'bcg=bcg:main'
        ]
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
)
