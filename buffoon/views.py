#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os.path
import random

import flask

from buffoon import app
import gamecore
from gamecore import GameError, FatalGameError

PROJECT_ROOT = os.path.dirname(__file__)
with open(os.path.join(PROJECT_ROOT, 'data', 'nouns.txt')) as inf:
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
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    gameserver.joinorcreategame(getplayer())
    return flask.redirect(flask.url_for('game'))


@app.route('/action/create', methods=['GET', 'POST'])
def create_game():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    try:
        humanplayers = int(flask.request.values.get('humanplayers', 1))
    except ValueError:
        humanplayers = 1
    try:
        aiplayers = int(flask.request.values.get('aiplayers', 0))
    except ValueError:
        aiplayers = 0

    totalplayers = humanplayers + aiplayers
    
    gameserver.creategame(getplayer(), minplayercount=totalplayers,
                          aicount=aiplayers)
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
            return flask.render_template('game-over.html', state=state)
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

@app.route('/json/startgame', methods=['GET', 'POST'])
def startgame():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
    try:
        ret = gameserver.startgame(getplayer())
        return flask.jsonify(status='ok', **ret)
    except GameError as e:
        return flask.jsonify(
            status='error',
            reason=unicode(e))

@app.route('/json/attempt')
def attempt():
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
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
    if 'playerid' not in flask.session:
        return flask.redirect(flask.url_for('main_page'))
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

# Ugly, but I don't understand better way for now :(
@app.route('/robots.txt')
def robots_txt():
    return flask.send_from_directory(os.path.join(PROJECT_ROOT, 'public'), 'robots.txt')
@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(PROJECT_ROOT, 'public'), 'favicon.png')
