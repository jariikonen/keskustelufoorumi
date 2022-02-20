from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from db import db
from constants import *
import auth

def validate_user_data(username, password1, password2):
    if username == '':
        return False, 'Käyttäjätunnus ei saa olla tyhjä!'
    if password1 != password2:
        return False, 'Salasanat eivät olleet samat!'
    return True, ''

def register(username, password):
    hash_value = None
    if password != '':
        hash_value = generate_password_hash(password)
    sql = """
        INSERT INTO users (username, password, role_id)
        VALUES (:username, :password, :role_id)
        RETURNING id as user_id, role_id
    """
    params = {
        'username':username, 'password':hash_value,
        'role_id': USER_ROLE__USER
    }
    try:
        row = db.session.execute(sql, params).fetchone()
        db.session.commit()
    except IntegrityError:
        return False, 'Käyttäjätunnus on jo käytössä!'
    membership_tuple = get_user_memberships(row.user_id)
    auth.set_user_session(row.user_id, username, row.role_id, membership_tuple)
    return True, ''

def get_user_memberships(user_id):
    sql = 'SELECT group_id FROM group_memberships WHERE user_id=:user_id'
    rows = db.session.execute(sql, {'user_id': user_id}).fetchall()
    membership_list = [3]   # Every user is member of ALL (group_id 3)
    for row in rows:
        membership_list.append(row.group_id)
    return tuple(membership_list)
