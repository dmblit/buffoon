#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import flask

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
        def quickstart(client):
            rv = client.get('/action/quickstart')
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/game')
        rv = quickstart(self.client1)

        rv = self.client2.get('/list')
        assert 'client1' in rv.data

        quickstart(self.client2)

        rv = self.client2.get('/game')
        assert 'client2' in rv.data
        assert 'Раунд 1' in rv.data

    def test_game_removal(self):
        def creategame(client):
            rv = client.post('/action/create', data = {
                'humanplayers': 2,
                'aiplayers': 1,
            })
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/game')

        creategame(self.client1)

        rv = self.client2.get('/list')
        assert 'client1' in rv.data
        self.assertEqual(rv.data.count('Подключиться'), 1)

        creategame(self.client1)

        rv = self.client2.get('/list')
        assert 'client1' in rv.data
        self.assertEqual(rv.data.count('Подключиться'), 1)

    def test_start_game(self):
        rv = self.client1.post('/action/create', data = {
            'humanplayers': 3,
        })
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/game')

        rv = self.client1.get('/game')
        assert 'Начать' in rv.data

        rv = self.client2.get('/action/quickstart')
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(dict(rv.header_list)['Location'], 'http://localhost/game')

        rv = self.client2.get('/game')
        assert 'Начать' not in rv.data

        rv = self.client2.post('/json/startgame')
        self.assertNotEqual(flask.json.loads(rv.data)['status'], 'ok')

        rv = self.client1.post('/json/startgame')
        self.assertEqual(flask.json.loads(rv.data)['status'], 'ok')

        for cl in [self.client1, self.client2]:
            rv = self.client1.get('/game')
            assert 'Раунд 1' in rv.data


