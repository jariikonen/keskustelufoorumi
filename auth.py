import secrets
from werkzeug.security import check_password_hash
from flask import render_template, request, session
from db import db
from constants import *
import users
import topics

def set_user_session(user_id, username, user_role, membership_tuple):
    session['user_id'] = user_id
    session['username'] = username
    session['user_role'] = user_role
    session['memberships'] = membership_tuple
    session['csrf_token'] = secrets.token_hex(16)

def login(username, password):
    sql = 'SELECT id, password, role_id FROM users WHERE username=:username'
    user = db.session.execute(sql, {'username': username}).fetchone()
    if user and user.role_id == USER_ROLE__DELETED:
        return False
    if user and user.password and password:
        if check_password_hash(user.password, password):
            membership_tuple = users.get_user_memberships(user.id)
            set_user_session(user.id, username, user.role_id, membership_tuple)
            return True
        return False
    elif user and not user.password and password == '':
        membership_tuple = users.get_user_memberships(user.id)
        set_user_session(user.id, username, user.role_id, membership_tuple)
        return True
    return False

def logout():
    if 'user_id' in session:
        del session['user_id']
    if 'username' in session:
        del session['username']
    if 'user_role' in session:
        del session['user_role']
    if 'memberships' in session:
        del session['memberships']
    if 'csrf_token' in session:
        del session['csrf_token']

def has_privilege(topic_id, privilege):
    topic_privileges = topics.get_topic_privileges(topic_id)[int(topic_id)]
    role = session.get('role')
    user_memberships = session.get('memberships', (GROUP_ID__ALL,))
    if role == USER_ROLE__SUPER or role == USER_ROLE__ADMIN:
        return topic_privileges
    for membership in user_memberships:
        if membership in topic_privileges.keys():
            if topic_privileges[membership][privilege]:
                return topic_privileges
    return False

def all_has_privilege(topic_id, privilege, topic_privileges=None):
    if not topic_privileges:
        topic_privileges = topics.get_topic_privileges(topic_id)[int(topic_id)]
    if GROUP_ID__ALL in topic_privileges.keys():
        if topic_privileges[GROUP_ID__ALL][privilege]:
            return True
    return False

def check_password(user_id, password):
    sql = 'SELECT password FROM users WHERE id=:user_id'
    password_row = db.session.execute(sql, {'user_id': user_id}).fetchone()
    if check_password_hash(password_row.password, password):
        return True
    return False

def is_authorized__edit_user(
        current_user_data, target_user_data, changing_elements_dict, form_data):
    if changing_elements_dict['username']:
        if not current_user_data['is_target']:
            return {
                'message': 'Vain käyttäjä itse voi muuttaa käyttäjänimeään',
                'response_code': HTTP_FORBIDDEN
            }
    if changing_elements_dict['password']:
        if not current_user_data['is_admin'] and not current_user_data['is_target']:
            return {
                'message': 'Tavallinen käyttäjä voi vaihtaa vain oman salasanansa',
                'response_code': HTTP_FORBIDDEN
            }
        if current_user_data['is_admin'] and not current_user_data['is_super']\
                and target_user_data['role_super']:
            return {
                'message': 'Ylläpitäjä ei voi vaihtaa pääkäyttäjän salasanaa',
                'response_code': HTTP_FORBIDDEN
            }
    if changing_elements_dict['role']:
        if current_user_data['is_target']:
            return {
                'message': 'Omaa rooliaan ei voi muuttaa',
                'response_code': HTTP_FORBIDDEN
            }
        if current_user_data['is_admin'] and not current_user_data['is_super']\
                and form_data['role'] == USER_ROLE__SUPER:
            return {
                'message': 'Ylläpitäjä ei voi tehdä käyttäjästä '\
                    + 'pääkäyttäjää',
                'response_code': HTTP_FORBIDDEN
            }
        if current_user_data['is_admin'] and not current_user_data['is_super']\
                and form_data['role'] > target_user_data['role_id']:
            return {
                'message': 'Ylläpitäjä ei voi alentaa käyttäjän roolia',
                'response_code': HTTP_FORBIDDEN
            }
