#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

Card = collections.namedtuple('Card', 'letter score')

DECKS = [
    [
        Card(u'н', 3),
        Card(u'и', 2),
        Card(u'к', 2),
        Card(u'т', 2),
        Card(u'е', 2),
        Card(u'о', 2),
        Card(u'а', 2),
    ], [
        Card(u'л', 3),
        Card(u'р', 3),
        Card(u'с', 3),
        Card(u'д', 4),
        Card(u'в', 3),
        Card(u'о', 2),
        Card(u'т', 3),
    ], [
        Card(u'д', 4),
        Card(u'п', 4),
        Card(u'а', 2),
        Card(u'к', 3),
        Card(u'б', 4),
        Card(u'м', 4),
        Card(u'ь', 4),
    ], [
        Card(u'р', 3),
        Card(u'и', 2),
        Card(u'ч', 4),
        Card(u'з', 4),
        Card(u'г', 4),
        Card(u'б', 4),
        Card(u'у', 4),
    ], [
        Card(u'ы', 5),
        Card(u'ш', 5),
        Card(u'ц', 4),
        Card(u'е', 2),
        Card(u'с', 3),
        Card(u'я', 4),
        Card(u'ж', 5),
    ], [
        Card(u'й', 6),
        Card(u'л', 3),
        Card(u'х', 5),
        Card(u'щ', 5),
        Card(u'ф', 5),
        Card(u'н', 3),
        Card(u'ё', 5),
    ], [
        Card(u'я', 4),
        Card(u'у', 4),
        Card(u'п', 4),
        Card(u'ю', 6),
        Card(u'в', 3),
        Card(u'э', 6),
        Card(u'ъ', 6),
    ],
]
