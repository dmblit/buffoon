#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

import gamecore

ROUND_TIME = 45
REST_TIME = 15

class GameClient(object):
    def __init__(self, allowedwords=frozenset(), deckfactory=gamecore.shuffled_cards):
        self.games = {} # gameid --> game
        self.players = {} # player --> game
        self.allowedwords = allowedwords
        self.deckfactory = deckfactory
        self.now = None
        self.nextservice = datetime.datetime.min
        self.serviceinterval = datetime.timedelta(minutes=1)

    #
    # Games management
    #

    def creategame(self, player, minplayercount=2):
        self.leavegame(player)
        game = Game(allowedwords=self.allowedwords,
                    cards=self.deckfactory(),
                    minplayercount=minplayercount)
        game.addplayer(player)
        game.updatestate(self.now)
        self.games[game.id()] = game
        self.players[player] = game
        return game.getstate(player)

    def joingame(self, player, gameid):
        self.leavegame(player)
        try:
            game = self.games[gameid]
            game.addplayer(player)
            game.updatestate(self.now)
            self.players[player] = game
            return game.getstate(player)
        except KeyError:
            raise gamecore.GameConnectionError()

    def joinorcreategame(self, player, **kwargs):
        self.leavegame(player)
        gamelist = self.listgames(player)['gamelist']
        for gamestate in gamelist:
            try:
                return self.joingame(player, gamestate['gameid'])
            except gamecore.GameConnectionError:
                pass
        return self.creategame(player, **kwargs)

    def listgames(self, player):
        gamelist = []
        for game in self.games.itervalues():
            game.updatestate(self.now)
            if game.iswaiting():
                gamelist.append(game.getstate(player))
        return {'gamelist': gamelist}

    def leavegame(self, player):
        try:
            game = self.players[player]
        except KeyError:
            return {}
        del self.players[player]
        game.removeplayer(player)
        game.updatestate(self.now)
        if game.empty():
            self._remove(game)
        return {}

    #
    # Game Actions
    #

    def getstate(self, player):
        game = self._getgame(player)
        game.updatestate(self.now)
        return game.getstate(player)

    def attempt(self, player, word):
        game = self._getgame(player)
        game.attempt(player, word)
        game.updatestate(self.now)
        return game.getstate(player)

    def choose(self, player, word):
        game = self._getgame(player)
        game.choose(player, word)
        game.updatestate(self.now)
        return game.getstate(player)

    def serviceifrequired(self, now):
        if self.nextservice is None or now >= self.nextservice:
            self._maintain()
            self.nextservice = now + self.serviceinterval

    #
    # Service
    #

    def _getgame(self, player):
        try:
            return self.players[player]
        except KeyError:
            raise gamecore.GameConnectionError()

    def _maintain(self, now=None):
        """ Remove old games. """
        if now is None:
            now = datetime.datetime.now()
        toremove = []
        for game in self.games.itervalues():
            if (game.empty() or
                game.isfinished() and now - game.finishtime() > self.KEEP_AFTER_FINISH):
                toremove.append(game)

        for game in toremove:
            self._remove(game)

    def _remove(self, game):
        del self.games[game.id()]
        for player in game:
            game.removeplayer(player)
            del game.players[player]


class Game(object):
    def __init__(self, allowedwords=frozenset(), cards=None,
                 creationtime=None, minplayercount=2):
        # settings
        self.minplayercount = minplayercount
        self.roundtime = datetime.timedelta(seconds=ROUND_TIME)
        self.resttime = datetime.timedelta(seconds=REST_TIME)

        # statistics
        if creationtime is None:
            creationtime = datetime.datetime.now()
        self.finishtime = None

        self.creationtime = creationtime
        self.rounds = []
        self.state = 'waiting'
        self.players = set()
        self.totalscore = {}
        self.allowedwords = allowedwords
        if cards is None:
            cards = [()] * 7
        self.cards = cards

    def addplayer(self, player):
        if self.iswaiting():
            self.players.add(player)
        else:
            raise gamecore.GameConnectionError()

    def removeplayer(self, player):
        self.players.remove(player)

    def choose(self, player, word):
        raise NotImplementedError

    def attempt(self, player, word):
        if not self.isround():
            raise gamecore.WrongStateError
        if not word in self.allowedwords:
            raise gamecore.BadWordError(word)

        score = gamecore.wordscore(self._curround().cards, word)
        self._curround().saveattempt(player, word, score)

    def getstate(self, player, now=None):
        def fromattempt(attempt):
            return {'word': attempt[0], 'score': attempt[1]}

        if now is None:
            now = datetime.datetime.now()

        ret = {
            'state': self.state,
            'players': list(sorted(self.players)),
            'gameid': self.id(),
        }

        if self.iswaiting():
            ret['playerstostart'] = self.minplayercount - len(self.players)
        elif self.isround() or self.isrest():
            ret['curround'] = self._curroundindex() + 1
            ret['millisecondsremains'] = int(self._secondsremains(now)) * 1000
            ret['totalscore'] = self._scorelist()
            if self.isround():
                ret['cards'] = self._getcurcards()
                lastattempt = self._curround().lastattempt(player)
                ret['lastattempt'] = fromattempt(lastattempt)
                bestattempt = self._curround().bestattempt(player)
                ret['bestattempt'] = fromattempt(bestattempt)
            else:
                usedwords = [
                    [player, fromattempt(self._curround().chosenattempt(player))]
                    for player in self.players]
                ret['usedwords'] = usedwords
        elif self.isover():
            ret['totalscore'] = self._scorelist()
            usedwords = [
                [player, fromattempt(self._curround().chosenattempt(player))]
                for player in self.players]
            ret['usedwords'] = usedwords
        else:
            assert False, "Unexpected state: {state}".format(state=self.state)
        return ret

    def updatestate(self, now=None):
        if now is None:
            now = datetime.datetime.now()
        while self._updatestate(now):
            pass

    def empty(self):
        return not self.players

    def iswaiting(self):
        return self.state == 'waiting'

    def isround(self):
        return self.state == 'round'

    def isrest(self):
        return self.state == 'rest'

    def isover(self):
        return self.state == 'gameover'

    def id(self):
        return id(self)

    def __iter__(self):
        return iter(self.players)

    #
    # private:
    #

    def _updatestate(self, now):
        if self.iswaiting():
            if len(self.players) >= self.minplayercount:
                self._newround(now)
                return True
        elif self.isround():
            if not self._secondsremains(now):
                self._finishround()
                if self._curroundindex() + 1 < self._totalrounds():
                    self._newrest()
                else:
                    self._gameover(now)
                return True
        elif self.isrest():
            if not self._secondsremains(now):
                self._newround(now)
                return True
        return False

    def _getcurcards(self):
        return self.cards[self._curroundindex()]

    def _curround(self):
        return self.rounds[-1]

    def _curroundindex(self):
        return len(self.rounds) - 1 

    def _scorelist(self):
        res = self.totalscore.items()
        res.sort(key=lambda x:x[1], reverse=True)
        return res

    def _newround(self, now):
        self.state = 'round'
        newroundindex = len(self.rounds)
        newround = Round(now=now)
        newround.endtime = now + self.roundtime
        newround.cards = self.cards[newroundindex]

        self.rounds.append(newround)

        for player in self.players:
            self.totalscore.setdefault(player, 0)

    def _finishround(self):
        for player in self.players:
            word, score = self._curround().chosenattempt(player)
            self.totalscore[player] += score

    def _newrest(self):
        self.state = 'rest'

    def _gameover(self, now):
        self.state = 'gameover'
        self.finishtime = now

    def _secondsremains(self, now):
        if self.isround():
            seconds = (self._curround().endtime - now).total_seconds()
        elif self.isrest():
            seconds = (self._curround().endtime + self.resttime - now).total_seconds()
        else:
            raise NotImplementedError
        if seconds < 0:
            seconds = 0
        return seconds

    def _totalrounds(self):
        return len(self.cards)

    def __repr__(self):
        return u"<Game id:'{id}', players:[{players}]>".format(
            id=self.id(), players=u', '.join(self.players))


class Round(object):
    def __init__(self, now, endtime=None, cards=None):
        self.now = now
        self.endtime = endtime
        self.attempts = {}
        self.cards = cards

    def lastattempt(self, player):
        if player not in self.attempts:
            return ('', 0)
        else:
            return self.attempts[player][-1]

    def bestattempt(self, player):
        if player not in self.attempts:
            return ('', 0)
        else:
            return max(self.attempts[player], key=lambda x: x[1])

    def saveattempt(self, player, word, score):
        attempt = (word, score)
        self.attempts.setdefault(player, []).append(attempt)

    def chosenattempt(self, player):
        return self.bestattempt(player)
