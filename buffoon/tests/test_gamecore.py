#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from buffoon import gamecore

class TestGameCore(unittest.TestCase):
    def test_wordscore(self):
        self.assertEqual(
            gamecore.wordscore([], u"слово"),
            0)
        self.assertEqual(
            gamecore.wordscore([(u'п', 4),
                                (u'а', 3),
                                (u'п', 4)],
                               u"попа"),
            7)

    def test_roundscore(self):
        self.assertEqual(
            gamecore.roundscore([], [u"слово", u"слово", u"воробей"]),
            [(u"слово", 0), (u"слово", 0), (u"воробей", 0)])
        self.assertEqual(
            gamecore.roundscore(
                [('p', 4), ('a', 3), ('p', 4)],
                ["popa", "popa", "pop"]),
            [6, 6, 5])

if __name__ == '__main__':
    unittest.main()
