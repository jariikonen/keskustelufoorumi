from sqlite3 import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session
from sqlalchemy.exc import IntegrityError
from db import db

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
        session['user_id'] = user_id
        session['username'] = username
        return True, ''
    except IntegrityError:
        return False, 'Käyttäjätunnus on jo käytössä!'

def login(username, password):
    sql = 'SELECT id, password FROM users WHERE username=:username'
    result = db.session.execute(sql, {'username':username})
    user = result.fetchone()
    if user:
        if check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = username
            return True
        else:
            return False
    else:
        return False
