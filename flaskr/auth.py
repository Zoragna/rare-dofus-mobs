import functools
import requests

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, make_response
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db


bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user["guest"]:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def get_server_name(cursor, s_id):
    cursor.execute('SELECT id,name FROM server WHERE id=%s', (s_id,))
    server = cursor.fetchone()
    return server[1]

@bp.before_app_request
def load_current_session():
    print("[DEBUG]","load logged in user")
    print("[DEBUG]","session ?", session)
    print("[DEBUG]","session type ?", type(session))
    print("[DEBUG]","new session ?", session.new)
    if "user" in g :
        print("g.user ?", g.user)
    else:
        print(g, "user" in g)

    server_id = session.get('server_id')
    user_id = session.get('user_id')
    cursor = get_db().cursor()

    if user_id is None:
        g.user = { "serverId" : session.get('server_id',3), "guest":True,
                   "locale": session.get("locale","fr") }
    else:
        cursor.execute(
            'SELECT id, username, metamob, serverId FROM account WHERE id = %s', (user_id,)
        )
        user = cursor.fetchone()
        g.user = { "id" : user[0], "username" : user[1], 
	                "metamob" : user[2], "serverId" : user[3],
			"guest":False }
    g.user["serverName"] = get_server_name(cursor, g.user["serverId"])
    print("Current session/context")
    print(g.user)

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        server_id = request.form['serverId']
        metamob = request.form['metamob']
        db = get_db()
        cursor = db.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif len(username) < 6 or len(username) > 30:
            error = 'Username should be between 6 and 29 characters.'
        if not password:
            error = 'Password is required.'
        elif len(password) < 6 or len(password) > 100:
            error = 'Password should be between 6 and 99 characters.'
        cursor.execute(
            'SELECT id FROM account WHERE username = %s', (username,)
        )
        if cursor.fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        cursor.execute('SELECT id FROM server WHERE id=%s', (server_id,))
        s_db = cursor.fetchone()
        if s_db is None:
            error = 'Server with id {} does not exist.'.format(server_id)

        # ex. www.metamob.fr/utilisateur/profil/Koolskaa
        if len(metamob) > 0:
            if not "metamob.fr/utilisateur/profil" in metamob :
                error = 'Not a metamob profile URL.'
            elif not requests.get(metamob).ok :
                error = 'Metamob profile does not exist.'

        if error is None:
            cursor.execute(
                'INSERT INTO account (username, password,metamob,serverId) VALUES (%s, %s, %s,%s)',
                (username, generate_password_hash(password), metamob, s_db[0])
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        error = None
        cursor.execute(
            'SELECT id, username, metamob, password FROM account WHERE username = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user[3], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user[0]
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/profile', methods=('GET',))
@bp.route('/profile/<username>')
@login_required
def profile(username=None):
    if username is None:
        return render_template('auth/my_profile.html')	
    else:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT username, metamob, server FROM account'
            ' WHERE username=%s', (username,))
        user = cursor.fetchone()
        profile = { "username":user[0], "metamob":user[1], "server":user[2] }
        return render_template('auth/a_profile.html', profile=profile)

@bp.route('/serv', methods=('POST',))
def change_server():
    print("[DEBUG]","change serv", request.form)
    if g.user["guest"]:
        g.user["serverId"] = request.form["server"]
        g.user["serverName"] = get_server_name(get_db().cursor(),request.form["server"])
        session["server_id"] = request.form["server"]
        session.modified = True
    else:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM server WHERE id=%s', (request.form["server"],))
        server = cursor.fetchone()
        cursor.execute(
                'UPDATE account SET serverId = %s'
                ' WHERE id = %s',
                (server[0], g.user['id'])
        )  
        db.commit()
    return make_response('{}', 200)


@bp.route('/lang', methods=('POST',))
def change_locale():
    print("[DEBUG auth] modify language", request.form)
    if g.user["guest"]:
       session["locale"] = request.form["language"]
       session.modified = True
    else:
       db = get_db()
       cursor = db.cursor()
       cursor.execute(
                'UPDATE account SET locale = %s'
                ' WHERE id = %s',
                (request.form["language"], g.user['id'])
       )
       db.commit()
    return make_response('{}', 200)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
