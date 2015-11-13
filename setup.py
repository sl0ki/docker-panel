#!/usr/bin/env python

import os
from setuptools import setup

REQUIREMENTS = [
    'docker-py==1.5.0',
    'gevent==1.0.2',
    'urwid==1.3.0',
]

setup(
    name="docker-panel",
    version="0.0.6",
    author="sl0ki",
    author_email="ruslano.prv@gmail.com",
    description=("A graphical terminal control panel for Docker."),
    license="GPLv3",
    keywords="docker control panel container cli",
    url="https://github.com/sl0ki/docker-panel",
    packages=['docker_panel'],
    entry_points={
        'console_scripts': [
            'docker-panel=docker_panel.cli:main',
        ],
    },
    install_requires=REQUIREMENTS,
)
