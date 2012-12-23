#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import gamecore

FIRST_NAMES = [
    u"Василий",
    u"Матвей",
    u"Фёдор",
    u"Иннокентий",
    u"Юлий",
    u"Фома",
    u"Казимир",
    u"Изя",
]

SECOND_NAMES = [
    u"Чаплыгин",
    u"Ладушкин",
    u"Георгиевич",
    u"Маркович",
    u"Альбертович",
    u"Жданович",
    u"Фокин",
    u"Огородников",
    u"Бобаль",
]

def generate_name():
    return random.choice(FIRST_NAMES) + u" " + random.choice(SECOND_NAMES)

def roundattempt(cards, allowedwords):
    if len(allowedwords) > 200:
        sample = random.sample(allowedwords, 200)
    else:
        sample = allowedwords
    return max(sample, key=lambda w: gamecore.wordscore(cards, w))

if __name__ == '__main__':
    curdir = os.path.dirname(__file__)
    with open(os.path.join(curdir, 'data', 'nouns.txt')) as inf:
        NOUNS = frozenset(
            line.strip().decode('utf-8') for line in inf)
    decks = gamecore.shuffled_cards()
    cards = decks[0]
    word = roundattempt(cards, NOUNS)
    print generate_name()
    print u' '.join(u'{0}({1})'.format(*c) for c in cards)
    print word
    print gamecore.wordscore(cards, word)


