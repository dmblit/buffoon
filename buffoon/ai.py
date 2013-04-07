#!/usr/bin/env python
# -*- coding: utf-8 -*-

import heapq
import os
import random
import gamecore

MALE_FIRST_NAMES = [
    u"Василий",
    u"Матвей",
    u"Фёдор",
    u"Иннокентий",
    u"Юлий",
    u"Фома",
    u"Казимир",
    u"Изя",
    u"Эраст",
]

MALE_SECONDS_NAMES = [
    u"Чаплыгин",
    u"Ладушкин",
    u"Георгиевич",
    u"Маркович",
    u"Альбертович",
    u"Жданович",
    u"Фокин",
    u"Огородников",
    u"Бобаль",
    u"Роальдович",
    u"Серафимович",
    u"Макарович",
]

FEMALE_FIRST_NAMES = [
    u"Изольда",
    u"Ингиборга",
    u"Мирабелла",
    u"Праскофья",
    u"Смиляна",
    u"Снежанна",
    u"Фёкла",
    u"Ярослава",
]

FEMALE_SECOND_NAMES = [
    u"Андрейко",
    u"Бабич",
    u"Вайсенберг",
    u"Гарфункель",
    u"Казимировна",
    u"Макаровна",
    u"Плоткина",
    u"Розенбаум",
    u"Сасько",
    u"Татьяновна",
    u"Тихомировна",
    u"Улановна",
]

class Fekla(object):
    cache = {}
    def __init__(self, allowedwords):
        if not isinstance(allowedwords, frozenset):
            raise ValueError
        if allowedwords in Fekla.cache:
            self.wordsbyalphabet = Fekla.cache[allowedwords]
        else:
            self.wordsbyalphabet = {}
            for word in allowedwords:
                for w in word:
                    s = self.wordsbyalphabet.setdefault(w, set())
                    s.add(word)
            Fekla.cache[allowedwords] = self.wordsbyalphabet

    def roundattempt(self, cards):
        c1, c2 = heapq.nlargest(2, cards, key=lambda c: c.score)
        l1, l2 = c1.letter, c2.letter
        best = (self.wordsbyalphabet[l1] & self.wordsbyalphabet[l2])
        if not best:
            best = self.wordsbyalphabet[l1]
        if len(best) > 10:
            best = heapq.nlargest(10, best,
                                  key=lambda w: (gamecore.wordscore(cards, w)) -len(w))
        else:
            best = list(best)
        return random.choice(best)

class Vasiliy(object):
    def __init__(self, allowedwords):
        self.allowedwords = allowedwords

    def roundattempt(self, cards):
        if len(self.allowedwords) > 200:
            sample = random.sample(self.allowedwords, 200)
        else:
            sample = self.allowedwords
        # we want short highscore words
        return max(sample,
                   key=lambda w: (gamecore.wordscore(cards, w), -len(w)))

class Vasserman(object):
    def __init__(self, allowedwords):
        self.allowedwords = allowedwords

    def roundattempt(self, cards):
        best, secondbest = -1, -1
        secondbestlist = []
        bestlist = []
        for word in self.allowedwords:
            score = gamecore.wordscore(cards, word)
            if score < secondbest:
                continue
            elif score == secondbest:
                secondbestlist.append(word)
            elif secondbest < score < best:
                secondbestlist = [word]
                secondbest = score
            elif score == best:
                bestlist.append(word)
            else:
                secondbest = best
                secondbestlist = bestlist
                best = score
                bestlist = [word]                
        return random.choice(secondbestlist)

def generate_name_ai(gender):
    m = {
        'male': (MALE_FIRST_NAMES, MALE_SECONDS_NAMES, Vasiliy),
        'female': (FEMALE_FIRST_NAMES, FEMALE_SECOND_NAMES, Fekla),
        'vasserman': ([u"Анатолий"], [u"Вассерман"], Vasserman),
    }
    first, second, cls = m[gender]
    return random.choice(first) + u" " + random.choice(second), cls


def generate_name(gender):
    first, second = {
        'male': (MALE_FIRST_NAMES, MALE_SECONDS_NAMES),
        'female': (FEMALE_FIRST_NAMES, FEMALE_SECOND_NAMES),
    }[gender]
    return random.choice(first) + u" " + random.choice(second)

if __name__ == '__main__':
    curdir = os.path.dirname(__file__)
    with open(os.path.join(curdir, 'data', 'nouns.txt')) as inf:
        NOUNS = frozenset(
            line.strip().decode('utf-8') for line in inf)
    decks = gamecore.shuffled_cards()
    cards = decks[0]
    for word in (Vasiliy(NOUNS).roundattempt(cards), Fekla(NOUNS).roundattempt(cards)):
        print generate_name('male')
        print u' '.join(u'{0}({1})'.format(*c) for c in cards)
        print word
        print gamecore.wordscore(cards, word)


