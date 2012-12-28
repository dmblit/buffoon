#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest
import buffoon

class BuffoonTestCase(unittest.TestCase):
    def setUp(self):
        dbname = buffoon.app.config['MONGODB_SETTINGS']['db']
        buffoon.db.connection.drop_database(dbname)

class TestNotLogged(BuffoonTestCase):
    def setUp(self):
        super(TestNotLogged, self).setUp()
        self.client = buffoon.app.test_client()

    def test_main_page(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)

    def test_game_url(self):
        for path in ['/game', '/create',
                     '/list',
                     '/action/quickstart',
                     '/action/create',
                     '/json/joingame',
                     '/json/attempt',
                     '/json/choose',
                     '/json/getgamestate']:
            rv = self.client.get(path)
            self.assertEqual(rv.status_code, 302, 'error on path {0}'.format(path))
            self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/')

class TestGameManagement(BuffoonTestCase):
    def setUp(self):
        super(TestGameManagement, self).setUp()
        self.client1 = buffoon.app.test_client()
        self.client = self.client1
        self.client2 = buffoon.app.test_client()

        self.client1.post('/login', data = {
            'playername': 'client1',
        })
        self.client2.post('/login', data = {
            'playername': 'client2',
        })

    def test_create(self):
        rv = self.client.get('/action/quickstart')
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/game')

        rv = self.client.get('/json/getgamestate')
        status = json.loads(rv.data)
        self.assertEqual(status['state'], 'waiting')

        rv = self.client2.get('/list')
        assert 'client1' in rv.data
