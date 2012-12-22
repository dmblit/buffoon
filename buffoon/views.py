#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os.path
import random

import flask

from buffoon import app
import gamecore
from gamecore import GameError, FatalGameError

curdir = os.path.dirname(__file__)
with open(os.path.join(curdir, 'data', 'nouns.txt')) as inf:
    NOUNS = frozenset(
        line.strip().decode('utf-8') for line in inf)

from mongoclient import BuffoonGame
gameserver = BuffoonGame(
    allowedwords=NOUNS,
    deckfactory=gamecore.shuffled_cards)

User = collections.namedtuple('User', 'playername playerid')

def getplayer():
    playername = flask.session['playername']
    playerid = flask.session['playerid']
    return User(playername, playerid)

@app.route('/')
def main_page():
    return flask.render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        # проверить, что имя ещё не занято
        playername = flask.request.form['playername']
        playerid = random.randint(0, 1000000)
        flask.session['playername'] = playername
        flask.session['playerid'] = playerid
        return flask.redirect(flask.url_for('main_page'))
    return flask.render_template('login.html')

@app.route('/logout')
def logout():
    if 'playername' in flask.session:
        # playername = flask.session['playername']
        del flask.session['playername']
        del flask.session['playerid']
        for key in flask.session.keys():
            del flask.session[key]
    return flask.redirect(flask.url_for('main_page'))

@app.route('/list')
def listofgames():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    res = gameserver.listgames(getplayer())
    if not res['gamelist']:
        return flask.render_template('game-list-no-games.html')
    else:
        return flask.render_template('game-list.html', gamelist = res['gamelist'])

@app.route('/action/quickstart')
def quickstart_game():
    gameserver.joinorcreategame(getplayer())
    return flask.redirect(flask.url_for('game'))

@app.route('/action/create', methods=['GET', 'POST'])
def create_game():
    players = int(flask.request.values.get('players', 2))
    gameserver.creategame(getplayer(), minplayercount=players)
    return flask.redirect(flask.url_for('game'))


@app.route('/game')
def game():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    try:
        state = gameserver.getstate(getplayer())
        if state['state'] == 'waiting':
            return flask.render_template('game-waiting.html', state=state)
        elif state['state'] == 'round':
            return flask.render_template('game-round.html', state=state)
        elif state['state'] == 'rest':
            return flask.render_template('game-rest.html', state=state)
        elif state['state'] == 'choosing':
            return flask.render_template('game-choosing.html', state=state)
        elif state['state'] == 'gameover':
            return flask.render_template('game-rest.html', state=state)
        return flask.render_template('game.html')
    except (GameError, FatalGameError):
        return flask.redirect(flask.url_for('main_page'))


@app.route('/json/getgamestate')
def getgamestate():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    reply = gameserver.getstate(getplayer())
    return flask.jsonify(reply)

@app.route('/json/joingame', methods=['GET', 'POST'])
def joingame():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    if 'gameid' not in flask.request.args:
        return flask.jsonify({'status': 'error',
                              'reason': 'no gameid'})
    try:
        gameserver.joingame(getplayer(), flask.request.args['gameid'])
        return flask.jsonify({'status': 'ok'})
    except (gamecore.GameError, gamecore.FatalGameError) as e:
        return flask.jsonify({'status': 'error',
                              'reason': unicode(e)})

@app.route('/json/attempt')
def attempt():
    if 'word' not in flask.request.args:
        return flask.jsonify({'reason': 'no word'})
    word = flask.request.args['word']
    try:
        state = gameserver.attempt(getplayer(), word.lower())
        return flask.jsonify(status='ok', **state)
    except GameError as e:
        return flask.jsonify(
            status='error',
            reason=unicode(e)
        )

@app.route('/json/choose')
def choose():
    if 'word' not in flask.request.args:
        return flask.jsonify({'reason': 'no word'})
    word = flask.request.args['word']
    try:
        state = gameserver.choose(getplayer(), word.lower())
        return flask.jsonify(status='ok', **state)
    except GameError as e:
        return flask.jsonify(
            status='error',
            reason=unicode(e)
        )

@app.route('/create')
def create_game_form():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    return flask.render_template('create-game-form.html')
