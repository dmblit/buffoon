#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))
os.execvp('python', ['python', '-m', 'unittest', 'discover', '-s', basedir])
