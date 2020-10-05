import functools
import requests
from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, make_response
)

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('capt', __name__)

def get_captures_today():
    db = get_db()
    capt_db = db.execute(
        'SELECT id, monsterId, captured, userId, proof'
        ' FROM capture ORDER BY captured DESC'
        ' LIMIT 5'
    ).fetchall()
    captures = []
    for capt in capt_db:
        monster = db.execute('SELECT id, nameFr FROM monster'
                             ' WHERE id='+str(capt["monsterId"])).fetchone()
        user = db.execute('SELECT id, username FROM user'
                          ' WHERE id='+str(capt["userId"])).fetchone()
        thumbs_up = db.execute('SELECT * FROM captureNote'
                               ' WHERE captureId=? AND value>0', (capt["id"],)).fetchall()
        thumbs_down = db.execute('SELECT * FROM captureNote'
                               ' WHERE captureId=? AND value<0', (capt["id"],)).fetchall()
        captures.append( {"id":capt["id"],
                          "monster":monster["nameFr"], 
                          "hunter":user["username"], 
                          "proof":capt["proof"],
                          "time":capt["captured"].strftime("%d %b %Y %Hh%M"),
                          "+":len(thumbs_up),
                          "-":len(thumbs_down)
        } )
    return captures

def get_archimonsters():
    return get_monsters(1)

def get_bandits():
    return get_monsters(3)

def get_notices():
    return get_monsters(2)

def get_monsters(m_type=0):
    db = get_db()
    mons_db = db.execute(
        'SELECT id, nameFr, img, zoneId, monsterType'
        ' FROM monster WHERE monsterType='+str(m_type)
    ).fetchall()
    now = datetime.now()
    monsters = []
    for mons in mons_db:
        m = db.execute(
            'SELECT id, captured '
            'FROM capture WHERE monsterId='+str(mons["id"])
        ).fetchone()
        monster = { "nameFr" : mons["nameFr"], "id":mons["id"]  }
        if m is None:
            monster["last capture"] = "Never recorded."
        else:
            s = (now-m["captured"]).total_seconds()
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            monster["last capture"] = str(hours)+" hours "+str(minutes)+" minutes ago"
        monsters.append(monster)
    return monsters

@bp.route('/')
def index():
    return render_template('capt/index.html', captures=get_captures_today(), 
        notices=get_notices(), bandits=get_bandits(), archimonsters=get_archimonsters())

@bp.route('/capture/<c_id>', methods=("POST",))
@login_required
def assess_capture(c_id=None):
    # TODO : try and use abort() instead of those two lines things
    if c_id is None:
        data = {'message': 'No capture ID provided', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    capture = get_db().execute('SELECT id FROM capture WHERE id=?', (c_id,)).fetchone()
    if capture is None:
        data = {'message': 'Capture ID not in database', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    value = 0
    if request.json is None or 'value' not in request.json:
        data = {'message': 'Request malformed', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    elif request.json['value'] == "+":
        value = 1
    elif request.json['value'] == "-":
        value = -1
    print(request.json, "value=", value) 
    note = get_db().execute('SELECT id,value FROM captureNote'
                            ' WHERE captureId=? AND userId=?', (c_id,g.user["id"])).fetchone()
    if not note is None and note["value"]*value >= 0 :
        print("note value",note["value"])
        data = {'message': 'User already assessed this capture.', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)

    db = get_db()
    if note is None :
        db.execute('INSERT INTO captureNote(captureId, userId, value) VALUES (?,?,?)',
               (c_id, g.user['id'],value))
    else:
        db.execute('UPDATE captureNote SET value = ?'
                   ' WHERE id = ?', (value, note["id"]))
    db.commit()
    thumbs_up = get_db().execute('SELECT id,value FROM captureNote'
                                 ' WHERE captureId=? AND value>0', (c_id,)
                ).fetchall()
    if thumbs_up is None:
        thumbs_up = []
    thumbs_down = get_db().execute('SELECT id,value FROM captureNote'
                                 ' WHERE captureId=? AND value<0', (c_id,)
                ).fetchall()
    if thumbs_down is None:
        thumbs_down = []
    data = {'thumbs_up':len(thumbs_up), 'thumbs_down':len(thumbs_down),
            'message': 'Assessed', 'code': 'SUCCESS'}
    return make_response(jsonify(data), 200)

@bp.route('/capture', methods=("POST",))
@login_required
def create_capture():
    user = g.user["username"]
    m_id = request.form['monsterId']
    date = request.form['date']
    time = request.form['time']
    proof = request.form['proof']

    capture_date = datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M")

    monster = get_db().execute(
        'SELECT id'
        ' FROM monster'
        ' WHERE id = ?',
        (m_id,)
    ).fetchone()

    now = datetime.now()

    if monster is None :
        data = {'message': 'Monster does not exist in the database.', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    elif not "https://www.dofus.com/fr/mmorpg/communaute/fincombat/" in proof :
        data = {'message': 'Proof should come from in-game screenshot', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    elif not requests.get(proof).ok :
        data = {'message': 'Proof page not found.', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    elif capture_date > now: 
        data = {'message': 'Can\'t create in the future', 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    else:
    # TODO : test if monster could have been captured
        db = get_db()
        db.execute(
           'INSERT INTO capture (monsterId, captured, userId, proof)'
           ' VALUES (?, ?, ?, ?)',
           (monster['id'], capture_date, g.user['id'], proof)
        )
        db.commit()
        data = {'message': 'Created', 'code': 'SUCCESS'}
        return make_response(jsonify(data), 200)

