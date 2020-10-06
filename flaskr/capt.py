import functools
import requests
from datetime import datetime, timedelta

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, make_response
)
from flask_babel import gettext

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('capt', __name__)


def get_captures_today():
    cursor = get_db().cursor()
    cursor.execute(
        'SELECT id, monsterId, captured, userId, proof'
        ' FROM capture ORDER BY captured DESC'
        ' LIMIT 5'
    )
    capt_db = cursor.fetchall()
    captures = []
    for capt in capt_db:
        c_id = capt[0]
        m_id = capt[1]
        u_id = capt[3]
        cursor.execute('SELECT id, nameFr FROM monster'
                             ' WHERE id=%s', (m_id,))
        monster = cursor.fetchone()
        cursor.execute('SELECT id, username FROM account'
                          ' WHERE id=%s', (u_id,))
        user = cursor.fetchone()
        cursor.execute('SELECT * FROM captureNote'
                            ' WHERE captureId=%s AND value>0', (c_id,))
        thumbs_up = cursor.fetchall()
        cursor.execute('SELECT * FROM captureNote'
                               ' WHERE captureId=%s AND value<0', (c_id,))
        thumbs_down = cursor.fetchall()
        captures.append( {"id":capt[0],
                          "monster":monster[1], 
                          "hunter":user[1], 
                          "proof":capt[2],
                          "time":capt[2].strftime("%d %b %Y %Hh%M"),
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
    cursor = db.cursor()
    cursor.execute(
        'SELECT id, nameFr, img, zoneId, monsterType'
        ' FROM monster WHERE monsterType=%s', (m_type,)
    )
    mons_db = cursor.fetchall()
    now = datetime.now()
    monsters = []
    for mons in mons_db:
        cursor.execute(
            'SELECT id, captured'
            ' FROM capture WHERE monsterId=%s', (mons[0],)
        )
        m = cursor.fetchone()
        monster = { "img":mons[2], "nameFr" : mons[1], "id":mons[0]  }
        if m is None:
            monster["last capture"] = "Never recorded."
        else:
            s = (now-m[1]).total_seconds()
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            monster["last capture"] = ""
            if hours != 0:
                monster["last capture"] += str(int(hours))+" hours "
            monster["last capture"] += str(int(minutes))+" minutes ago"
        monsters.append(monster)
    return monsters

@bp.route('/')
def index():
    return render_template('capt/index.html', captures=get_captures_today(), 
        notices=get_notices(), bandits=get_bandits(), archimonsters=get_archimonsters())

@bp.route('/useful_links')
def useful_links():
    return render_template('capt/useful_links.html')

@bp.route('/capture/<c_id>', methods=("POST",))
@login_required
def assess_capture(c_id=None):
    db = get_db()
    cursor = db.cursor()
    # TODO : try and use abort() instead of those two lines things
    if c_id is None:
        data = {'message': gettext('No capture ID provided'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    cursor.execute('SELECT id FROM capture WHERE id=%s', (c_id,))
    capture = cursor.fetchone()
    if capture is None:
        data = {'message': gettext('Capture ID not in database'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    value = 0
    if request.json is None or 'value' not in request.json:
        data = {'message': gettext('Request malformed'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)
    elif request.json['value'] == "+":
        value = 1
    elif request.json['value'] == "-":
        value = -1
    cursor.execute('SELECT id,value FROM captureNote'
                            ' WHERE captureId=%s AND userId=%s', (c_id,g.user["id"]))
    note = cursor.fetchone()
    if not note is None and note[1]*value >= 0 :
        data = {'message': gettext('User already assessed this capture.'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 400)

    if note is None :
        cursor.execute('INSERT INTO captureNote(captureId, userId, value) VALUES (%s,%s,%s)',
               (c_id, g.user['id'],value))
    else:
        cursor.execute('UPDATE captureNote SET value = %s'
                   ' WHERE id = %s', (value, note[0]))
    db.commit()
    cursor.execute('SELECT id,value FROM captureNote'
                                 ' WHERE captureId=%s AND value>0', (c_id,)
                )
    thumbs_up = cursor.fetchall()
    if thumbs_up is None:
        thumbs_up = []
    cursor.execute('SELECT id,value FROM captureNote'
                                 ' WHERE captureId=%s AND value<0', (c_id,)
                )
    thumbs_down = cursor.fetchall()
    if thumbs_down is None:
        thumbs_down = []
    data = {'thumbs_up':len(thumbs_up), 'thumbs_down':len(thumbs_down),
            'message': 'Assessed', 'code': 'SUCCESS'}
    return make_response(jsonify(data), 200)

def get_monster(m_id, cursor):
    cursor.execute(
        'SELECT id, nameFr, monsterType'
        ' FROM monster'
        ' WHERE id = %s',
        (m_id,)
    )
    return cursor.fetchone()


@bp.route('/capture', methods=("POST",))
@login_required
def create_capture():
    user = g.user["username"]
    m_id = request.form['monsterId']
    date = request.form['date']
    time = request.form['time']
    proof = request.form['proof']

    capture_date = datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M")

    cursor = get_db().cursor()
    monster = get_monster(m_id, cursor)

    now = datetime.now()
    cursor = get_db().cursor()
    cursor.execute(
        'SELECT id, monsterId, captured, userId, proof'
        ' FROM capture WHERE monsterId=%s'
        ' ORDER BY captured DESC', (m_id,)
    )   
    your_last_capture = cursor.fetchone()

    if monster is None :
        data = {'message': gettext('Monster does not exist in the database.'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 404)
    
    cursor = get_db().cursor()
    cursor.execute('SELECT minRes FROM monsterType WHERE Seq=%s', (monster[2],))
    min_res = timedelta(hours=cursor.fetchone()[0])

    if not "https://www.dofus.com/fr/mmorpg/communaute/fincombat/" in proof :
        data = {'message': gettext('Proof should come from in-game screenshot'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 403)
    elif not requests.get(proof).ok :
        data = {'message': gettext('Proof page not found.'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 404)
    elif capture_date > now: 
        data = {'message': gettext('Can\'t create in the future'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 403)
    elif not your_last_capture is None and your_last_capture[2] + min_res > capture_date:
        data = {'message': gettext('You coudln\'t have captured this monster.'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 403)
    else:
        db = get_db()
        db.cursor().execute(
           'INSERT INTO capture (monsterId, captured, userId, proof)'
           ' VALUES (%s, %s, %s, %s)',
           (monster[0], capture_date, g.user['id'], proof)
        )
        db.commit()
        data = {'message': 'Created', 'code': 'SUCCESS'}
        return make_response(jsonify(data), 200)

@bp.route('/monster/<m_id>')
@login_required
def track_monster(m_id=None):
    if m_id is None:
        data = {'message': gettext('No ID provided'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 403)
    db = get_db()
    cursor = db.cursor() 
    monster = get_monster(m_id, cursor)
    if monster is None:
        data = {'message': gettext('No monster has this id.'), 'code': 'FAILURE'}
        return make_response(jsonify(data), 404)

    cursor = get_db().cursor()
    cursor.execute(
        'SELECT id, monsterId, captured, userId, proof'
        ' FROM capture WHERE monsterId=%s'
        ' ORDER BY captured DESC', (m_id,)
    )
    capt_db = cursor.fetchall()
    captures = []
    for capt in capt_db:
        c_id = capt[0]
        u_id = capt[3]
        cursor.execute('SELECT id, username FROM account'
                       ' WHERE id=%s', (u_id,))
        user = cursor.fetchone()
        cursor.execute('SELECT * FROM captureNote'
                       ' WHERE captureId=%s AND value>0', (c_id,))
        thumbs_up = cursor.fetchall()
        cursor.execute('SELECT * FROM captureNote'
                       ' WHERE captureId=%s AND value<0', (c_id,))
        thumbs_down = cursor.fetchall()
        captures.append( {"id":capt[0],
                          "monster":monster[1],
                          "hunter":user[1],
                          "proof":capt[2],
                          "time":capt[2].strftime("%d %b %Y %Hh%M"),
                          "+":len(thumbs_up),
                          "-":len(thumbs_down)
        } )

    return render_template('capt/monster.html', 
        captures=captures, nameFr=monster[1],
        bandits=get_bandits(), notices=get_notices(), archimonsters=get_archimonsters()
    )
