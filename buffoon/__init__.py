#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import flask

from flask.ext.mongoengine import MongoEngine

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'qwerty'
app.config['MONGODB_SETTINGS'] = {
    'db': 'buffoon_game',
    'host': os.environ.get('MONGOHQ_URL', 'mongodb://localhost:27017/buffoon_game')
}

db = MongoEngine(app)

import buffoon.views
