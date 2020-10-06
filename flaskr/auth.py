import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, make_response
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        cursor = get_db().cursor()
        cursor.execute(
            'SELECT id, username, metamob FROM account WHERE id = %s', (user_id,)
        )
        user = cursor.fetchone()
        g.user = { "id" : user[0], "username" : user[1], "metamob" : user[2] }

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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

        # ex. www.metamob.fr/utilisateur/profil/Koolskaa
        # TODO : check page exists | user is registered
        if len(metamob) > 0 and not "metamob.fr/utilisateur/profil" in metamob :
            error = 'Invalid metamob profile URL.'

        if error is None:
            cursor.execute(
                'INSERT INTO account (username, password,metamob) VALUES (%s, %s, %s)',
                (username, generate_password_hash(password), metamob)
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
            'SELECT username, metamob FROM account'
            ' WHERE username=%s', (username,))
        user = cursor.fetchone()
        profile = { "username":user[0], "metamob":user[1] }
        return render_template('auth/a_profile.html', profile=profile)

@bp.route('/lang', methods=('POST',))
@login_required
def change_locale():
    db = get_db()
    cursor = db.cursor()
    print(request.form)
    session["locale"] = request.form["language"]
    return make_response('{}', 200)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
