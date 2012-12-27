#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import copy
import decks
import heapq
from itertools import imap
import random

def wordscore(cards, word, allowNegative=False):
    """Calculate the score of the word."""
    cards = list(cards)
    cards.sort(key=lambda x: x[1], reverse=True)

    ret = 0
    for l in word:
        for i, c in enumerate(cards):
            if c[0] == l:
                ret += c[1]
                del cards[i]
                break
    ret -= len(word)
    if not allowNegative and ret < 0:
        ret = 0
    return ret

def roundscore(cards, words):
    """Calculate all scores of the words."""
    wordcount = collections.Counter(words)
    if len(words) < 2:
        longest = None
    else:
        longest, secondlongest = heapq.nlargest(2, imap(len, words))
        if secondlongest == longest:
            longest = None
    result = []
    for word in words:
        score = wordscore(cards, word, allowNegative=True) - (wordcount[word] - 1)
        if len(word) == longest:
            score += 1
        if score < 0:
            score = 0
        result.append(score)
    return result

def shuffled_cards():
    """
    Return list of tupeles of cards, shuffled and ready to play.
    
    Each tuple of the list is a set of cards for one round.
    """
    curdecks = copy.deepcopy(decks.DECKS)
    for deck in curdecks:
        random.shuffle(deck)
    return zip(*curdecks)

class GameError(Exception):
    pass

class WrongStateError(GameError):
    def __init__(self):
        GameError.__init__(self, u"Действие не может быть выполнено в данный момент.")

class BadWordError(GameError):
    def __init__(self, word):
        GameError.__init__(self, u"Слова '{word}' не существует.".format(word=word))

class BadChoiceError(GameError):
    pass


class FatalGameError(Exception):
    pass

class AlreadyInGameError(FatalGameError):
    def __init__(self, player):
        FatalGameError.__init__(self, u"Игрок {player} уже в другой игре.".format(player=player))

class GameConnectionError(FatalGameError):
    def __init__(self):
        FatalGameError.__init__(self, u"Невозможно подключиться к выбранной игре.")

if __name__ == '__main__':
    print roundscore([('c', 3), ('c', 3)], ['cc', 'c'])

