import secrets
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session
from sqlalchemy.exc import IntegrityError
from db import db

def set_user_session(user_id, username):
    session['user_id'] = user_id
    session['username'] = username
    session['csrf_token'] = secrets.token_hex(16)

def validate_user_data(username, password1, password2):
    if username == '':
        return False, 'Käyttäjätunnus ei saa olla tyhjä!'
    if password1 != password2:
        return False, 'Salasanat eivät olleet samat!'
    return True, ''

def register(username, password):
    hash_value = generate_password_hash(password)
    sql = '''
        INSERT INTO users (username, password)
        VALUES (:username, :password)
        RETURNING id
    '''
    try:
        result = db.session.execute(sql, {'username':username, 'password':hash_value})
        user_id = result.fetchone()[0]
        db.session.commit()
        set_user_session(user_id, username)
        return True, ''
    except IntegrityError:
        return False, 'Käyttäjätunnus on jo käytössä!'

def login(username, password):
    sql = 'SELECT id, password FROM users WHERE username=:username'
    result = db.session.execute(sql, {'username':username})
    user = result.fetchone()
    if user and user.password and password:
        if check_password_hash(user.password, password):
            set_user_session(user.id, username)
            return True
        else:
            return False
    elif user and not user.password and password == '':
        set_user_session(user.id, username)
        return True
    else:
        return False

def logout():
    if 'user_id' in session:
        del session['user_id']
    if 'username' in session:
        del session['username']
    if 'csrf_token' in session:
        del session['csrf_token']
