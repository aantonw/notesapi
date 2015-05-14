#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    notesapi
    ~~~~~
    RESTful notes api with flask
"""

__author__  = 'aantonw'
__version__ = '0.0.1'

import os
from flask import Flask, abort, jsonify, make_response, request, g
from flask_httpauth import HTTPBasicAuth
import sqlite3


app = Flask(__name__)
# set default config
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '/tmp/db_notesapi.db'),
    DEBUG=True,
    BAUSR='anton',
    BAPWD='thisisasecretpassword',
))

def dict_factory(cursor, row):
    ''' make sqlite3.Row as dict '''
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def db_connect():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = dict_factory
    return conn

def db_get():
    if not hasattr(g, '_notesapi_db'):
        # attach connection to app context
        g._notesapi_db = db_connect()
    return g._notesapi_db

def db_init():
    with app.app_context():
        db = db_get()
        c = db.cursor()
        c.execute('DROP TABLE IF EXISTS notes')
        c.execute('''CREATE TABLE notes (
          id      INTEGER  PRIMARY KEY autoincrement,
          title   CHAR(50) NOT NULL,
          content TEXT     NOT NULL
        )''')
        notes = [('pertama', 'ini content dari note pertama'),
                 ('kedua', 'ini content dari note kedua')]
        c.executemany('INSERT INTO notes (title, content) VALUES (?, ?)', notes)
        db.commit()

@app.teardown_appcontext
def teardown_db(exeption):
    if hasattr(g, '_notesapi_db'):
        g._notesapi_db.close()

auth = HTTPBasicAuth()
# auth default
@auth.get_password
def get_password(username):
    if username == app.config['BAUSR']:
        return app.config['BAPWD']
    return None

@app.route('/')
@auth.login_required
def index():
    resp = make_response("""RESTful notes api available end points:
[GET] /api/notes 
    -> show all available notes\n
[GET] /api/notes/<note_id> 
    -> show note with id note_id\n
[POST] /api/notes 
    -> add new note\n
[PUT] /api/notes/<note_id> 
    -> update note based on note_id\n
[DELETE] /appi/notes/<note_id> 
    -> delete note based on note_id\n
    """)
    # resp.headers['Content-Type'] = 'text/plain';
    return resp

@app.route('/api/notes', methods=['GET'])
@auth.login_required
def get_notes():
    db = db_connect()
    cur = db.execute('SELECT title, content FROM notes ORDER BY id DESC')
    dbnotes = cur.fetchall()
    return jsonify({'notes': dbnotes})

def note_byid(db, note_id):
    cur = db.execute('SELECT title, content FROM notes WHERE id=?', [note_id])
    return cur.fetchone()

@app.route('/api/notes/<int:note_id>', methods=['GET'])
@auth.login_required
def get_note(note_id):
    db = db_get()
    dbnote = note_byid(db, note_id)
    if dbnote is None:
        return abort(404)
    return jsonify({'notes': dbnote})

@app.route('/api/notes', methods=['POST'])
@auth.login_required
def create_note():
    if not request.json or not 'title' in request.json:
        abort(400)
    note = {
        'title': request.json['title'],
        'content': request.json.get('content', '')
    }
    db = db_get()
    db.execute('INSERT INTO notes (title, content) VALUES (?, ?)',
                 [note['title'], note['content']])
    db.commit()
    return jsonify({'notes': note}), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@auth.login_required
def update_note(note_id):
    db = db_get()
    dbnote = note_byid(db, note_id)
    if dbnote is None:
        return abort(404)
    if not request.json:
        abort(400)
    if not 'title' in request.json or not 'content' in request.json:
        abort(400)
        
    note = {
        'title': request.json['title'],
        'content': request.json.get('content', '')
    }
    db.execute('UPDATE notes SET title=?, content=? WHERE id=?', 
            [note['title'], note['content'], note_id])
    db.commit()
    return jsonify({'notes': note})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@auth.login_required
def delete_note(note_id):
    db = db_get()
    dbnote = note_byid(db, note_id)
    if dbnote is None:
        return abort(404)
    db.execute('DELETE FROM notes WHERE id=?', [note_id])
    db.commit()
    return jsonify({'result': True})

@app.errorhandler(404)
def page_not_found(error):
    return make_response(jsonify({'error': 'not found'})), 404

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'bad request'})), 400

@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'method not allowed'})), 405
    
@auth.error_handler
def unauthorized():
    return jsonify({'error': 'unauthorized access'})

if __name__ == '__main__':
    db_init()
    app.run()
