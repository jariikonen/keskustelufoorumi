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
    print('SET_USER_SESSION: ', session)

def login(username, password):
    sql = 'SELECT id, password, role_id FROM users WHERE username=:username'
    user = db.session.execute(sql, {'username': username}).fetchone()
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
