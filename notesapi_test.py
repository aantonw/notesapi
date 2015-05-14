#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    notesapi test
    ~~~~~
    testing for RESTful notes api with flask
"""

__author__  = 'aantonw'
__version__ = '0.0.1'

import os
import notesapi
import base64
import unittest
import tempfile
import json
import re

class NotesapiTestCase(unittest.TestCase):

    def setUp(self):
        ''' Set up a blank db before each test '''
        self.db_file, notesapi.app.config['DATABASE'] = tempfile.mkstemp()
        notesapi.app.config['TESTING'] = True
        self.app = notesapi.app.test_client()
        
        # explicitly make an application context with app_context()
        with notesapi.app.app_context():
            notesapi.db_init()

    def tearDown(self):
        ''' close db and remove tempfile after earch test '''
        os.close(self.db_file)
        os.unlink(notesapi.app.config['DATABASE'])

    def with_basicauth(self, method, url, data=None, content_type=None):
        ''' request with basic auth '''
        return self.app.open(url, method=method,
            headers={
                'Authorization': 'Basic ' + \
                base64.b64encode(notesapi.app.config['BAUSR'] + \
                    ':' + notesapi.app.config['BAPWD'])
            },
            follow_redirects=True,
            data=data,
            content_type=content_type
        )

    def test_getindex(self):
        resp = self.app.get('/')
        # FIXME: resp.status_code should be 400 not 200
        jdata = json.loads(resp.data)
        self.assertEqual(jdata['error'], 'unauthorized access')
        
        resp = self.with_basicauth('GET', '/')
        self.assertEqual(resp.status_code, 200)
        self.assertRegexpMatches(resp.data, re.compile(r'^RESTful notes api'))

    def test_getnotes(self):
        resp = self.with_basicauth('GET', '/api/notes')
        jdata = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(jdata['notes']), 2)

    def test_getnote(self):
        # try to get note with id 1
        resp = self.with_basicauth('GET', '/api/notes/1')
        jdata = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(jdata['notes']['title'], 'pertama')
        self.assertEqual(jdata['notes']['content'], 'ini content dari note pertama')
        
        # try to get unavailable note
        resp = self.with_basicauth('GET', '/api/notes/12')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', json.loads(resp.data))

    def test_addnote(self):
        # try to add a new note
        postdata = {
            'title': 'edit test note',
            'content': 'edit note from unit test'
        }
        resp = self.with_basicauth('POST', '/api/notes',
            data=json.dumps(postdata),
            content_type='application/json'
        )
        jdata = json.loads(resp.data)
        self.assertNotIn('error', jdata)
        self.assertEqual(jdata['notes']['title'], postdata['title'])
        self.assertEqual(jdata['notes']['content'], postdata['content'])
        self.assertEqual(resp.status_code, 201)
        
        # check available note(s)
        resp = self.with_basicauth('GET', '/api/notes')
        jdata = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(jdata['notes']), 3)
        
        # try to add a new note, but not specify mimetype or Content-Type header
        resp = self.with_basicauth('POST', '/api/notes',
            data=json.dumps(postdata) # no mimetype header
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', json.loads(resp.data))
    
    def test_editnote(self):
        # try to update note with id 2
        editdata = {
            'title': 'edit test note',
            'content': 'edit note from unit test'
        }
        resp = self.with_basicauth('PUT', '/api/notes/2',
            data=json.dumps(editdata),
            content_type='application/json'
        )
        jdata = json.loads(resp.data)
        self.assertNotIn('error', jdata)
        self.assertEqual(jdata['notes']['title'], editdata['title'])
        self.assertEqual(jdata['notes']['content'], editdata['content'])
        self.assertEqual(resp.status_code, 200)
        
        # try to update unavailable note
        resp = self.with_basicauth('PUT', '/api/notes/23',
            data=json.dumps(editdata),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', json.loads(resp.data))
    
    def test_deletenote(self):
        # try to delete note with id 2
        resp = self.with_basicauth('DELETE', '/api/notes/2')
        jdata = json.loads(resp.data)
        self.assertNotIn('error', jdata)
        self.assertEqual(jdata['result'], True)
        self.assertEqual(resp.status_code, 200)
        
        # check available note(s)
        resp = self.with_basicauth('GET', '/api/notes')
        jdata = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(jdata['notes']), 1)
        
        # check deleted note
        resp = self.with_basicauth('GET', '/api/notes/2')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', json.loads(resp.data))

if __name__ == '__main__':
    unittest.main()
