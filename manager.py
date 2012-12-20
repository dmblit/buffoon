#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from flask.ext.script import Manager, Server

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))
from buffoon import app

manager = Manager(app)

manager.add_command("runserver",
                    Server(use_debugger = True,
                           use_reloader = True,
                           host = '0.0.0.0'))

if __name__ == '__main__':
    manager.run()
