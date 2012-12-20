#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import flask

from flask.ext.mongoengine import MongoEngine

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'qwerty'
app.config['MONGODB_DB'] = os.environ.get('MONGOHQ_URL', 'buffoon_game')

db = MongoEngine(app)

import buffoon.views
