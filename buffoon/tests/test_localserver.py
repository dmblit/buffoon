#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import unittest

if __name__ == '__main__':
    import sys
    sys.path.append('../..')

from buffoon import localserver

class TestGame(unittest.TestCase):
    def test_addplayer(self):
        game = localserver.Game(minplayercount=2)
        game.addplayer('user1')
        state = game.getstate('user1')
        self.assertEqual(state['state'], 'waiting')
        self.assertEqual(state['playerstostart'], 1)

    def test_removeplayer(self):
        game = localserver.Game(minplayercount=3)
        game.addplayer('user1')
        game.addplayer('user2')
        game.removeplayer('user1')
        game.removeplayer('user2')
        self.assertTrue(game.empty())


class TestRound(unittest.TestCase):
    def test_attempt(self):
        n = datetime.datetime.now()
        r = localserver.Round(n, n, [])
        self.assertEqual(r.lastattempt('user'), ('', 0))
        self.assertEqual(r.bestattempt('user'), ('', 0))

        r.saveattempt('user', 'foo', 5)
        self.assertEqual(r.lastattempt('user'), ('foo', 5))
        r.saveattempt('user', 'bar', 4)
        self.assertEqual(r.lastattempt('user'), ('bar', 4))

        self.assertEqual(r.bestattempt('user'), ('foo', 5))

class TestGameClient(unittest.TestCase):
    def test_joinorcreate(self):
        client = localserver.GameClient()
        client.joinorcreategame('user', minplayercount=2)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'waiting')
        self.assertEqual(state['playerstostart'], 1)

        client.joinorcreategame('user2', minplayercount=3)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'round')

    def test_typicalgame(self):
        client = localserver.GameClient(
            allowedwords=frozenset(['foo', 'bar']),
            deckfactory=lambda : [(('f', 10), ('o', 10)),
                                  (('b', 20), ('a', 20))])

        client.now = datetime.datetime(2000, 1, 1, 0, 0, 0)
        client.joinorcreategame('user', minplayercount=2)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'waiting')

        client.joinorcreategame('user2', minplayercount=2)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'round')

        state = client.attempt('user', 'foo')
        self.assertEqual(state['lastattempt']['word'], 'foo')
        self.assertEqual(state['bestattempt']['word'], 'foo')

        state = client.attempt('user', 'bar')
        self.assertEqual(state['lastattempt']['word'], 'bar')
        self.assertEqual(state['bestattempt']['word'], 'foo')

        client.now += datetime.timedelta(seconds=localserver.ROUND_TIME)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'rest')
        totalscore = dict(state['totalscore'])
        self.assertTrue('user' in totalscore)
        self.assertTrue('user2' in totalscore)
        self.assertTrue(totalscore['user'] > totalscore['user2'])
        self.assertTrue('usedwords' in state)

        client.now += datetime.timedelta(seconds=localserver.REST_TIME)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'round')

        client.now += datetime.timedelta(seconds=localserver.ROUND_TIME)
        state = client.getstate('user')
        self.assertEqual(state['state'], 'gameover')

    def test_leavegame(self):
        client = localserver.GameClient(
            allowedwords=frozenset(['foo', 'bar']),
            deckfactory=lambda : [(('f', 10), ('o', 10)),
                                  (('b', 20), ('a', 20))])
        state1 = client.creategame('user', minplayercount=2)
        gameid1 = state1['gameid']
        # put second player so game will not be deleted
        client.joinorcreategame('user2')

        state2 = client.creategame('user', minplayercount=2)
        gameid2 = state2['gameid']
        self.assertNotEqual(gameid1, gameid2)

if __name__ == '__main__':
    unittest.main()
