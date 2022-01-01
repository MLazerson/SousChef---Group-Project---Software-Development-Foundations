import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from application.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'Username {} is already taken.'.format(username)
        elif db.execute(
            'SELECT id FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = 'Email {} is already taken.'.format(email)

        if error is None:
            db.execute(
                'INSERT INTO user (username, email, password) VALUES (?, ?, ?)',
                (username, email, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    
    return render_template('registerSousChef.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('home_page'))
        
        flash(error)
    
    return render_template('loginSousChef.html')
    
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
    
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)
    
    return wrapped_view

@bp.route('/resetpass', methods=('GET', 'POST'))
def resetpass():
    if request.method == 'POST':
        cur_username = request.form['username']
        curr_email = request.form['email']
        new_password = request.form['newpassword']
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM user WHERE username = ? AND email = ?', (cur_username,curr_email,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username or email.'
        elif not new_password:
            error = 'Must enter a new password!'
        
        if error is None:
            flash(generate_password_hash(new_password))
            db.execute(
                'UPDATE user SET password = ? WHERE username = ?', (generate_password_hash(new_password), cur_username)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('ResetPassword.html')

@bp.route('/deleteacct', methods=('GET', 'POST'))
@login_required
def confirm_del():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            # check that ID exists
            acct = db.execute(
                'SELECT id FROM user WHERE username = ? AND password = ?', (username, generate_password_hash(password))
            )
            # HERE BE ACCOUNT DELETION CODE
            if acct is not None:
                #"delete user"
                db.execute(
                    'DELETE FROM user WHERE username = ? AND password = ?', 
                    (user['username'], user['password'])
                )
                db.commit()
                # after account deleted, clear session
                session.clear()
                return redirect(url_for('home_page'))
        
        flash(error)
    
    return render_template('acctdel.html')