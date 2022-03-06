from flask import session
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from db import db
from constants import *
import auth

def validate_username(username):
    if len(username) < MIN_USERNAME:
        return {
            'message': 'Käyttäjätunnuksen on oltava vähintään '\
                + f'{MIN_USERNAME} merkin mittainen',
            'response_code': HTTP_BAD_REQUEST
        }
    if len(username) > MAX_PASSWORD:
        return {
            'message': 'Käyttäjätunnus saa olla enintään '\
                + f'{MAX_USERNAME} merkin mittainen',
            'response_code': HTTP_BAD_REQUEST
        }
    return False

def validate_passwords(password1, password2):
    if password1 != password2:
        return {
            'message': 'Salasanat eivät olleet samat',
            'response_code': HTTP_BAD_REQUEST
        }
    if len(password1) < MIN_PASSWORD:
        return {
            'message': 'Salasanan on oltava vähintään '\
                + f'{MIN_PASSWORD} merkin mittainen',
            'response_code': HTTP_BAD_REQUEST
        }
    if len(password2) > MAX_PASSWORD:
        return {
            'message': 'Salasana saa olla enintään '\
                + f'{MAX_PASSWORD} merkin mittainen',
            'response_code': HTTP_BAD_REQUEST
        }
    return False

def validate_user_data(username, password1, password2):
    error_dict = validate_username(username)
    if error_dict:
        return error_dict
    error_dict = validate_passwords(password1, password2)
    if error_dict:
        return error_dict
    return False

def validate_user_data__edit_user(changin_elements_dict, form_data):
    if changin_elements_dict['username']:
        error_dict = validate_username(form_data['username'])
        if error_dict:
            return error_dict
    if changin_elements_dict['password']:
        error_dict = validate_passwords(
            form_data['new_password1'], form_data['new_password2'])
        if error_dict:
            return error_dict
    return False

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
        'username': username, 'password': hash_value,
        'role_id': USER_ROLE__USER
    }
    try:
        row = db.session.execute(sql, params).fetchone()
        db.session.commit()
    except IntegrityError:
        return {
            'message': 'Käyttäjätunnus on jo käytössä',
            'response_code': HTTP_FORBIDDEN
        }
    membership_tuple = get_user_memberships(row.user_id)
    auth.set_user_session(row.user_id, username, row.role_id, membership_tuple)
    return False

def get_user_memberships(user_id):
    sql = 'SELECT group_id FROM group_memberships WHERE user_id=:user_id'
    rows = db.session.execute(sql, {'user_id': user_id}).fetchall()
    membership_list = [3]   # Every user is member of ALL (group_id 3)
    for row in rows:
        membership_list.append(row.group_id)
    return tuple(membership_list)

def get_user_data(user_id):
    sql = """
        SELECT id, username, role_id, registered_at
        FROM users WHERE id=:user_id
    """
    return db.session.execute(sql, {'user_id': user_id}).fetchone()

def get_user_groups(user_id):
    sql = """
        SELECT GM.group_id, G.group_name
        FROM group_memberships GM JOIN groups G
            ON G.id=GM.group_id
        WHERE GM.user_id=:user_id;
    """
    row_list = db.session.execute(sql, {'user_id': user_id}).fetchall()
    group_list = []
    for row in row_list:
        group_list.append(f'{row["group_name"]} ({row["group_id"]})')
    if len(group_list) == 0:
        return '-'
    return ', '.join(group_list)

def get_current_user_data(target_id):
    current_user = session.get('user_id')
    current_role = session.get('user_role')
    return {
        'current_user': current_user,
        'current_role': current_role,
        'is_target': current_user == target_id,
        'is_admin': current_role == USER_ROLE__ADMIN\
            or current_role == USER_ROLE__SUPER,
        'is_super': current_role == USER_ROLE__SUPER
    }

def get_target_user_data(target_row):
    target_role_user = True\
        if target_row['role_id'] == USER_ROLE__USER else False
    target_role_admin = True\
        if target_row['role_id'] == USER_ROLE__ADMIN else False
    target_role_super = True\
        if target_row['role_id'] == USER_ROLE__SUPER else False
    target_role_deleted = True\
        if target_row['role_id'] == USER_ROLE__DELETED else False
    return {
        'user_id': target_row.id,
        'username': target_row.username,
        'role_id': target_row.role_id,
        'role_user': target_role_user,
        'role_admin': target_role_admin,
        'role_super': target_role_super,
        'role_deleted': target_role_deleted
    }

def find_changing_elements__edit_user(target_user_data, form_data):
    changing_elements_dict = {}
    if target_user_data['username'] != form_data['username']:
        changing_elements_dict['username'] = True
    else:
        changing_elements_dict['username'] = False
    if form_data['new_password1'] != '' or form_data['new_password2'] != '':
        changing_elements_dict['password'] = True
    else:
        changing_elements_dict['password'] = False
    if target_user_data['role_id'] != int(form_data['role']):
        changing_elements_dict['role'] = True
    else:
        changing_elements_dict['role'] = False
    return changing_elements_dict

def update_user_data_all(user_id, username, role_id, password):
    hash_value = generate_password_hash(password)
    sql = """
        UPDATE users
        SET username=:username, password=:hash_value, role_id=:role_id
        WHERE id=:user_id
        RETURNING id
    """
    params = {
        'username': username, 'hash_value': hash_value, 'role_id': role_id,
        'user_id': user_id
    }
    row = db.session.execute(sql, params).fetchone()
    db.session.commit()
    if row:
        return False
    error_dict = {
        'message': 'Käyttäjää ei löytynyt', 'response_code': HTTP_NOT_FOUND
    }
    return error_dict

def update_username_and_role(user_id, username, role_id):
    sql = """
        UPDATE users
        SET username=:username, role_id=:role_id
        WHERE id=:user_id
        RETURNING id
    """
    params = {'username': username, 'role_id': role_id, 'user_id': user_id}
    row = db.session.execute(sql, params).fetchone()
    db.session.commit()
    if row:
        return False
    return {
        'message': 'Käyttäjää ei löytynyt', 'response_code': HTTP_NOT_FOUND
    }

def get_success_message__edit_user(changin_elements_dict, form_data):
    message_parts = []
    if changin_elements_dict['username']:
        message_parts.append(
            f'käyttäjänimeksi vaihdettiin {form_data["username"]}')
    if changin_elements_dict['password']:
        message_parts.append('salasana vaihdettiin')
    if changin_elements_dict['role']:
        if int(form_data['role']) == USER_ROLE__USER:
            message_parts.append('käyttäjä on nyt tavallinen käyttäjä')
        elif int(form_data['role']) == USER_ROLE__ADMIN:
            message_parts.append('käyttäjä on nyt ylläpitäjä')
        elif int(form_data['role']) == USER_ROLE__SUPER:
            message_parts.append('käyttäjä on nyt pääkäyttäjä')
    return 'Käyttäjätietojen muokkaus onnistui: ' + ', '.join(message_parts)

def count_other_super(user_id):
    sql = f"""
        SELECT COUNT(id) FROM users
        WHERE role_id={USER_ROLE__SUPER}
            AND NOT id=:user_id
    """
    return db.session.execute(sql, {'user_id': user_id}).fetchone()[0]

def create_pending_delete(user_id):
    sql = """
        INSERT INTO pending_user_deletions (user_id)
        VALUES (:user_id)
    """
    db.session.execute(sql, {'user_id': int(user_id)})
    sql = 'UPDATE users SET role_id=:role_id WHERE id=:user_id'
    db.session.execute(
        sql, {'role_id': USER_ROLE__DELETED, 'user_id': user_id})
    db.session.commit()

def delete_user(user_id):
    sql = 'DELETE FROM users WHERE id=:user_id'
    try:
        db.session.execute(sql, {'user_id': user_id})
    except IntegrityError:
        db.session.rollback()
        create_pending_delete(user_id)
    db.session.commit()

def get_user_list():
    sql = 'SELECT id, username, role_id, registered_at FROM users'
    return db.session.execute(sql).fetchall()

def get_group_list():
    sql = 'SELECT id, group_name FROM groups WHERE id NOT IN (1,2,3)'
    return db.session.execute(sql).fetchall()

def group_add(user_list, group):
    sql = """
        INSERT INTO group_memberships (group_id, user_id)
        VALUES (:group_id, :user_id)
    """
    for user in user_list:
        try:
            db.session.execute(sql, {'group_id': group, 'user_id': user})
        except IntegrityError:
            db.session.rollback()
            return {
                'message': f'Käyttäjää ({user}) tai ryhmää ({group}) ei ole',
                'response_code': HTTP_NOT_FOUND}
    db.session.commit()
