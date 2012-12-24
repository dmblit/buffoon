#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from itertools import izip
import logging
import random

from mongoengine import Q

import ai
import gamecore
import decks
from buffoon import db

ROUND_TIME = 45
CHOOSING_TIME = 10
REST_TIME = 10

class BuffoonGame(object):
    def __init__(self, allowedwords=frozenset(),
                 deckfactory=gamecore.shuffled_cards):
        self.allowedwords = allowedwords
        self.deckfactory = deckfactory
        self.maxidletime = datetime.timedelta(minutes=15)

    def creategame(self, player, minplayercount=2, aicount=0):
        if not isinstance(player, (str, unicode)):
            player = player.playername

        if aicount > minplayercount:
            raise ValueError, "AIs count exceeds players limit o_O"
        self._maintain()
        self.leavegame(player)

        game = Game()
        game.settings.playercount = minplayercount
        game.players.append(player)

        game.cards =  []
        curdeck = self.deckfactory()
        for roundcards in curdeck:
            game.cards.append([])
            l = game.cards[-1]
            for card in roundcards:
                l.append(GameCard(letter=card.letter, score=card.score))

        for __ in xrange(aicount):
            ainame = None
            while not ainame or game.hasplayer(ainame):
                gender = random.choice(('male', 'female'))
                ainame = ai.generate_name(gender)
            attemptlst = []
            cls = {'male': ai.Vasiliy, 'female': ai.Fekla}[gender]
            aiplayer = cls(self.allowedwords)
            for roundcards in curdeck:
                word = aiplayer.roundattempt(roundcards)
                attemptlst.append(word)
            game.aiattempts[ainame] = attemptlst
            game.addplayer(ainame)

        game.save()
        return game.getstate(player)

    def joingame(self, player, gameid):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        self._maintain()
        self.leavegame(player)

        game = Game.objects(id=gameid).first()
        if game is not None:
            game.addplayer(player)
            return game.getstate(player)
        else:
            raise gamecore.GameConnectionError()

    def joinorcreategame(self, player, **kwargs):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        self._maintain()
        self.leavegame(player)

        gamelist = self.listgames(player)['gamelist']
        for gamestate in gamelist:
            try:
                return self.joingame(player, gamestate['gameid'])
            except gamecore.GameConnectionError:
                pass
        return self.creategame(player, **kwargs)

    def listgames(self, player):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        gamelist = []
        self._maintain()
        for game in Game.objects(state='waiting'):
            game.updatestate()
            if game.iswaiting():
                gamelist.append(game.getstate(player))
        return {'gamelist': gamelist}
    
    def leavegame(self, player):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        for game in Game.objects(players=player):
            game.removeplayer(player)
        return {}

    def getstate(self, player):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        game = self._getgame(player)
        game.updatestate()
        return game.getstate(player)

    def attempt(self, player, word):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        if word.lower() not in self.allowedwords:
            raise gamecore.BadWordError(word)
        game = self._getgame(player)
        game.attempt(player, word)
        game.updatestate()
        return game.getstate(player)

    def choose(self, player, word):
        if not isinstance(player, (str, unicode)):
            player = player.playername
        game = self._getgame(player)
        game.choose(player, word)
        game.updatestate()
        return game.getstate(player)

    @staticmethod
    def _getgame(player):
        game = Game.objects(players=player).first()
        if game is None:
            raise gamecore.GameConnectionError()
        return game

    def _maintain(self, now=None):
        if now is None:
            now = datetime.datetime.now()
        Game.objects(Q(players__size=0) | Q(state='gameover')).delete()
        keepthreshold = now - self.maxidletime
        Game.objects(Q(state='waiting') &
                     Q(createtime__lte=keepthreshold)).delete()
        Game.objects(Q(state__ne='waiting') &
                     Q(firstround_starttime__lte=keepthreshold)).delete()
        

# Game server that stores its state in mongo db instance.

class GameSettings(db.EmbeddedDocument):
    # how many players will participate in the game
    playercount = db.IntField(required=True)

    # how many AIs will participate in the game
    aicount = db.IntField(required=True, default=lambda: 0)

    # how long round will last
    roundseconds = db.IntField(required=True)

    # how long rest between rounds will last
    restseconds = db.IntField(required=True)

    choosingseconds = db.IntField(required=True, default=lambda: 0)

    def __unicode__(self):
        return u'<GameSettings: players: {0}>'.format(self.playercount)

    def rounddelta(self):
        return datetime.timedelta(seconds=self.roundseconds)

    def restdelta(self):
        return datetime.timedelta(seconds=self.restseconds)

    def choosingdelta(self):
        return datetime.timedelta(seconds=self.choosingseconds)

    def fullrounddelta(self):
        return self.rounddelta() + self.choosingdelta() + self.restdelta()

def _replace(query, obj):
    replace_dict = {}
    for k in obj:
        if k != 'id':
            replace_dict['set__' + k] = obj[k]
    ret = query.update_one(**replace_dict)
    assert ret <= 1
    return ret

def _atomic(f):
    def atomic_f(self, *args, **kwargs):
        if self.id is None:
            return f(self, *args, **kwargs)

        if not self.version:
            q = Game.objects(id=self.id).update(set__version=1)

        for i in xrange(10):
            if i:
                logging.warning('Attempt #{0} of {1}'.format(i + 1, f.func_name))
            self.reload()
            res = f(self, *args, **kwargs)
            oldversion = self.version
            self.version += 1
            q = Game.objects(Q(id=self.id) & Q(version=oldversion))
            replaced = _replace(q, self)
            if replaced:
                return res
    return atomic_f

class Game(db.Document):
    version = db.IntField(default=lambda :0)

    createtime = db.DateTimeField(default=datetime.datetime.now, required=True)

    firstround_starttime = db.DateTimeField()

    # settings of the game set at game start
    settings = db.EmbeddedDocumentField(
        'GameSettings', required=True,
        default=lambda:GameSettings(playercount=2,
                                    roundseconds=ROUND_TIME,
                                    restseconds=REST_TIME,
                                    choosingseconds=CHOOSING_TIME))

    # players (including ais) that are currently in the game
    players = db.ListField(db.StringField(), default=[])

    # attempts of ai players for all rounds
    aiattempts = db.MapField(db.ListField(db.StringField()), default=dict)

    # current total score of the players, updated after each round
    totalscore = db.MapField(db.IntField(), default={})

    # statistics about completed rounds and round that is currently in progress
    rounds = db.ListField(db.EmbeddedDocumentField('GameRound'), default=list)

    # all the cards that will be in the game,
    # 1st element is the cards for 1st round , etc.
    cards = db.ListField(db.ListField(db.EmbeddedDocumentField('GameCard')),
                         default=list)

    # current state of the game, one of: 
    #  waiting, round, rest, gameover
    state = db.StringField(required=True, default=lambda :'waiting')

    def __unicode__(self):
        return u'<Game: players: [{0}] state: {1}>'.format(
            ', '.join(self.players), self.state)

    @_atomic
    def addplayer(self, player):
        if len(self.players) >= self.settings.playercount:
            raise gamecore.GameConnectionError()
        if not self.iswaiting():
            raise gamecore.GameConnectionError()
        if player not in self.players:
            self.players.append(player)

    @_atomic
    def removeplayer(self, player):
        try:
            self.players.remove(player)
        except ValueError:
            pass

    @_atomic
    def choose(self, player, word):
        if not self.ischoosing():
            raise gamecore.WrongStateError
        self._curround().choose(player, word)

    @_atomic
    def attempt(self, player, word):
        return self._attempt(player, word)

    def _attempt(self, player, word):
        if not self.isround():
            raise gamecore.WrongStateError
        score = gamecore.wordscore(self._curcards(), word)
        self._curround().saveattempt(player, word, score)

    @_atomic
    def updatestate(self, now=None):
        if now is None:
            now = datetime.datetime.now()
        while self._updatestate(now):
            pass

    def getstate(self, player, now=None):
        def fromattempt(attempt):
            return {'word': attempt.word, 'score': attempt.score,
                    'finalscore': attempt.finalscore}

        if now is None:
            now = datetime.datetime.now()

        ret = {
            'state': self.state,
            'players': list(sorted(self.players)),
            'gameid': str(self.id),
        }

        if self.iswaiting():
            ret['playerstostart'] = self.settings.playercount - len(self.players)
        elif self.isround() or self.isrest() or self.ischoosing():
            ret['curround'] = self._curroundindex() + 1
            ret['secondsremains'] = int(self._secondsremains(now))
            ret['totalscore'] = self._scorelist()
            if self.isround():
                ret['cards'] = self._curcards()
                lastattempt = self._curround().lastattempt(player)
                ret['lastattempt'] = fromattempt(lastattempt)
                bestattempt = self._curround().bestattempt(player)
                ret['bestattempt'] = fromattempt(bestattempt)
                ret['secondstotal'] = self.settings.roundseconds
            elif self.isrest():
                ret['secondstotal'] = self.settings.restseconds
                ret['usedwords'] = [
                    [p, fromattempt(self._curround().chosenattempt(p))]
                    for p in self.players]
            elif self.ischoosing():
                ret['secondstotal'] = self.settings.choosingseconds
                ret['roundattempts'] = [fromattempt(attempt)
                                        for attempt in sorted(self._curattempts(player),
                                                              key=lambda x: x.score,
                                                              reverse=True)]
                ret['chosenattempt'] = fromattempt(
                    self._curround().chosenattempt(player))
            else:
                raise AssertionError, "WTF?"
        elif self.isover():
            ret['totalscore'] = self._scorelist()
            ret['usedwords'] = [
                [player, fromattempt(self._curround().chosenattempt(player))]
                for player in self.players]
            ret['history'] = self._gethistory()
        else:
            assert False, "Unexpected state: {state}".format(state=self.state)
        return ret

    def isround(self):
        return self.state == 'round'

    def iswaiting(self):
        return self.state == 'waiting'

    def isrest(self):
        return self.state == 'rest'

    def isover(self):
        return self.state == 'gameover'

    def ischoosing(self):
        return self.state == 'choosing'

    def empty(self):
        return not self.players

    def hasplayer(self, player):
        return player in self.players

    def _gethistory(self):
        res = []
        for idx, rnd in enumerate(self.rounds):
            entry = {
                'round': idx + 1,
                'cards': self._cards(idx)
            }
            entry['usedwords'] = getusedwords(rnd)
            res.append(entry)
        return res

    def _updatestate(self, now):
        if self.iswaiting():
            if len(self.players) >= self.settings.playercount:
                self._newround(now)
                return True
        elif self.isround():
            if not self._secondsremains(now):
                self.state = 'choosing'
        elif self.ischoosing():
            if not self._secondsremains(now):
                self._finishround()
                if self._curroundindex() + 1 < self._totalrounds():
                    self._newrest()
                else:
                    self._gameover()
                return True
        elif self.isrest():
            if not self._secondsremains(now):
                self._newround(now)
                return True
        return False

    def _newround(self, now):
        self.state = 'round'
        self.rounds.append(GameRound())

        if self.totalscore is None:
            self.totalscore = {}

        for player in self.players:
            self.totalscore.setdefault(player, 0)

        if self.firstround_starttime is None:
            self.firstround_starttime = now

        curround = self._curroundindex()
        for ai, attemptlst in self.aiattempts.iteritems():
            if len(attemptlst) > curround:
                self._attempt(ai, attemptlst[curround])

    def _finishround(self):
        curround = self._curround()
        words = []
        for player in self.players:
            if not curround.haschosen(player):
                curround.chosedefault(player)
            words.append(curround.chosenattempt(player).word)
        scores = gamecore.roundscore(self._curcards(), words)
        scores = dict(izip(words, scores))
        for player in self.players:
            chosenattempt = curround.chosenattempt(player)
            chosenattempt.finalscore = scores[chosenattempt.word]

        for player in self.players:
            chosenattempt = curround.chosenattempt(player)
            self.totalscore[player] += chosenattempt.score

    def _newrest(self):
        self.state = 'rest'

    def _gameover(self):
        self.state = 'gameover'

    def _totalrounds(self):
        return len(self.cards)

    def _scorelist(self):
        res = self.totalscore.items()
        res.sort(key=lambda x:x[1], reverse=True)
        return res

    def _secondsremains(self, now):
        if self.isround():
            endtime = (
                self.firstround_starttime + self.settings.rounddelta() +
                self._curroundindex() * (self.settings.fullrounddelta()))
        elif self.ischoosing():
            endtime = (
                self.firstround_starttime + self.settings.rounddelta() +
                + self.settings.choosingdelta() +
                self._curroundindex() * (self.settings.fullrounddelta()))
        elif self.isrest():
            endtime = (self.firstround_starttime +
                       (self._curroundindex() + 1) * (
                           self.settings.fullrounddelta()))
        else:
            raise NotImplementedError
        seconds = (endtime - now).total_seconds()
        if seconds < 0:
            seconds = 0
        return seconds
            
    def _curround(self):
        return self.rounds[-1]

    def _curroundindex(self):
        if not self.rounds:
            raise ValueError, "Rounds didn't started yet"
        return len(self.rounds) - 1

    def _curcards(self):
        return self._cards(self._curroundindex())

    def _cards(self, roundindex):
        return [decks.Card(card.letter, score=card.score)
                for card in self.cards[roundindex]]

    def _curattempts(self, player):
        return self._curround().attempts.get(player, [])

class GameCard(db.EmbeddedDocument):
    letter = db.StringField(max_length=1, min_length=1)
    score = db.IntField()

    def __unicode__(self):
        return u'<Card: letter: {0} score: {1}>'.format(self.letter, self.score)

class GameRound(db.EmbeddedDocument):
    attempts = db.MapField(db.ListField(db.EmbeddedDocumentField('Attempt')),
                           default=dict)

    chosen = db.MapField(db.EmbeddedDocumentField('Attempt'), default=dict)

    def saveattempt(self, player, word, score):
        # TODO: проверять, что список не слишком длинный
        lst = self.attempts.setdefault(player, [])
        if all(a.word != word for a in lst):
            a = Attempt(word=word, score=score)
            if len(lst) >= 100:
                lst[-1] = a
            else:
                lst.append(a)

    def lastattempt(self, player):
        playerattempts = self.attempts.get(player, None)
        if not playerattempts:
            return Attempt(word='', score=0)
        return playerattempts[-1]

    def bestattempt(self, player):
        playerattempts = self.attempts.get(player, None)
        if not playerattempts:
            return Attempt(word='', score=0)
        return max(playerattempts, key=lambda a: a.score)

    def chosenattempt(self, player):
        try:
            return self.chosen[player]
        except KeyError:
            return self.bestattempt(player)

    def haschosen(self, player):
        return player in self.chosen

    def chosedefault(self, player):
        """Chose random word among words with high score."""
        assert player not in self.chosen
        bestattempt = self.bestattempt(player)

        if bestattempt.score == 0:
            self.chosen[player] = self.bestattempt(player)
            return
            
        allthebest = [a for a in self.attempts.get(player, ())
                      if a.score == bestattempt.score]
        self.chosen[player] = random.choice(allthebest)

    def choose(self, player, word):
        playerattempts = self.attempts.get(player, ())
        for attempt in playerattempts:
            if attempt.word == word:
                self.chosen[player] = attempt
                break
        else:
            raise gamecore.BadChoiceError
    
    def iterchosen(self):
        return self.chosen.iteritems()

class Attempt(db.EmbeddedDocument):
    word = db.StringField(required=True)
    score = db.IntField(required=True)
    finalscore = db.IntField()

    def __unicode__(self):
        return u'<Attempt: word: {0} score: {1}>'.format(self.word, self.score)

def tostate(attempt):
    if isinstance(attempt, Attempt):
        return {'word': attempt.word, 'score': attempt.score,
                'finalscore': attempt.finalscore}
    else:
        raise ValueError, 'Unknown attempt type'

def getusedwords(rnd):
    if not isinstance(rnd, GameRound):
        raise ValueError, 'expected rnd to be GameRound'
    usedwords = []
    for player, attempt in rnd.iterchosen():
        usedwords.append({
            'player': player,
            'word': attempt.word,
            'score': attempt.score,
            'finalscore': attempt.finalscore
        })
    return usedwords
