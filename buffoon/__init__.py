#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import flask

from flask.ext.mongoengine import MongoEngine

logging.basicConfig(level=logging.INFO)

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'qwerty'
app.config['MONGODB_SETTINGS'] = {
    'db': 'buffoon_game',
    'host': os.environ.get('MONGOHQ_URL', 'localhost'),
}

db = MongoEngine(app)

import buffoon.views
