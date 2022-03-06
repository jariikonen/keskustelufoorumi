from sqlalchemy.exc import IntegrityError
from db import db
from constants import *

def get_topics():
    return db.session.execute(
        'SELECT id, topic, description, created_at FROM topics ORDER BY id'
    ).fetchall()

def get_topic(topic_id):
    sql = """
        SELECT id, topic, description, created_at
        FROM topics WHERE id=:topic_id
    """
    return db.session.execute(sql, {'topic_id': topic_id}).fetchone()

def get_topics_with_privileges():
    sql = """
        SELECT T.id, T.topic, T.description, TP.know_priv AS group_know,
            TP.read_priv AS group_read, TP.write_priv AS group_write,
            TP_ALL.know_priv as all_know, TP_ALL.read_priv AS all_read,
            TP_ALL.write_priv AS all_write
        FROM topics T, groups G, topic_privileges TP, topic_privileges TP_ALL
        WHERE G.group_name=T.topic AND TP.group_id=G.id
            AND TP_ALL.group_id=:group_all AND TP_ALL.topic_id=T.id
    """
    return db.session.execute(sql, {'group_all': GROUP_ID__ALL}).fetchall()

def get_topic_with_privileges(topic_id):
    sql = """
        SELECT T.id, T.topic, T.description, TP.know_priv AS group_know,
            TP.read_priv AS group_read, TP.write_priv AS group_write,
            TP_ALL.know_priv as all_know, TP_ALL.read_priv AS all_read,
            TP_ALL.write_priv AS all_write
        FROM topics T, groups G, topic_privileges TP, topic_privileges TP_ALL
        WHERE G.group_name=T.topic AND TP.group_id=G.id
            AND TP_ALL.group_id=:group_all AND TP_ALL.topic_id=T.id
            AND T.id=:topic_id
    """
    return db.session.execute(
        sql, {'group_all': GROUP_ID__ALL, 'topic_id': topic_id}).fetchone()

# Used by get_all_topic_privileges() and get_topic_privileges()
def get_privilege_dict(row_list):
    privilege_dict = {}
    for row in row_list:
        if row.topic_id not in privilege_dict.keys():
            privilege_dict[row.topic_id] = {row.group_id: {}}
        else:
            privilege_dict[row.topic_id][row.group_id] = {}
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_KNOW]\
            = row.know_priv
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_READ]\
            = row.read_priv
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_WRITE]\
            = row.write_priv
    return privilege_dict

def get_all_topic_privileges():
    sql = """
        SELECT T.id AS topic_id, TP.group_id, TP.know_priv, TP.read_priv,
            TP.write_priv
        FROM topic_privileges TP, topics T, groups G
        WHERE T.id=TP.topic_id
            AND G.id=TP.group_id
        ORDER BY topic_id
    """
    row_list = db.session.execute(sql).fetchall()
    return get_privilege_dict(row_list)

def get_topic_privileges(topic_id):
    sql = """
        SELECT T.id AS topic_id, TP.group_id, TP.know_priv, TP.read_priv,
            TP.write_priv
        FROM topic_privileges as TP, topics T, groups G
        WHERE TP.topic_id=T.id
            AND G.id=TP.group_id
            AND T.id=:topic_id
        ORDER BY topic_id
    """
    row_list = db.session.execute(sql, {'topic_id': topic_id}).fetchall()
    return get_privilege_dict(row_list)

def get_secret_topics(topic_list, topic_privileges, user_memberships, user_role):
    secret_topics = []
    if user_role == USER_ROLE__USER and len(user_memberships) == 1\
            and GROUP_ID__ALL in user_memberships:
        return None
    if user_role == USER_ROLE__ADMIN\
            or user_role == USER_ROLE__SUPER:
        for topic in topic_list:
            if GROUP_ID__ALL not in topic_privileges[topic.id]:
                secret_topics.append(topic)
        return secret_topics

def get_num_of_threads(topics):
    thread_nums = {}
    for topic in topics:
        result = db.session.execute(
            'SELECT COUNT(*) FROM messages WHERE refers_to IS NULL AND topic_id=:id',
            {'id': topic.id}
        )
        thread_nums[topic.id] = result.fetchone()[0]
    return thread_nums

def get_num_of_messages(topics):
    message_nums = {}
    for topic in topics:
        result = db.session.execute(
            'SELECT COUNT(*) FROM messages WHERE topic_id=:id',
            {'id': topic.id}
        )
        message_nums[topic.id] = result.fetchone()[0]
    return message_nums

def get_time_of_latest_message(topics):
    latest_message_times = {}
    for topic in topics:
        result = db.session.execute(
            'SELECT MAX(sent_at) FROM messages WHERE topic_id=:id',
            {'id': topic.id}
        )
        latest_message_times[topic.id] = result.fetchone()[0]
        if latest_message_times[topic.id]:
            latest_message_times[topic.id]\
                = latest_message_times[topic.id].strftime('%d.%m.%Y klo %H:%M')
        else:
            latest_message_times[topic.id] = '-'
    return latest_message_times

def new_topic(topic_dict):
    sql_insert_topic = """
        INSERT INTO topics (topic, description)
        VALUES (:topic, :description)
        RETURNING id
    """
    sql_insert_group = """
        INSERT INTO groups (group_name)
        VALUES (:topic)
        RETURNING id
    """
    sql_insert_privileges_all = """
        INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
        VALUES (:group_id_ALL, :topic_id, :all_know, :all_read, :all_write)
    """
    sql_insert_privileges_group = """
        INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
        VALUES (:group_id, :topic_id, :group_know, :group_read, :group_write)
    """
    try:
        topic_id = db.session.execute(sql_insert_topic, topic_dict).fetchone()[0]
    except IntegrityError:
        db.session.rollback()
        return {
            'message': 'Aihealue on jo olemassa',
            'response_code': HTTP_FORBIDDEN}
    topic_dict['topic_id'] = topic_id
    group_id = db.session.execute(sql_insert_group, topic_dict).fetchone()[0]
    topic_dict['group_id_ALL'] = GROUP_ID__ALL
    topic_dict['group_id'] = group_id
    db.session.execute(sql_insert_privileges_all, topic_dict)
    db.session.execute(sql_insert_privileges_group, topic_dict)
    db.session.commit()
    return False

def form_topic_dict(form_dict, topic_id=None):
    topic_dict = {}
    if topic_id:
        topic_dict['topic_id'] = topic_id
    topic_dict['topic'] = form_dict.get('topic')
    topic_dict['description'] = form_dict.get('description')
    topic_dict['all_know'] = True if 'privileges_all_know' in form_dict\
        else False
    topic_dict['all_read'] = True if 'privileges_all_read' in form_dict\
        else False
    topic_dict['all_write'] = True if 'privileges_all_write' in form_dict\
        else False        
    topic_dict['group_know'] = True if 'privileges_group_know' in form_dict\
        else False
    topic_dict['group_read'] = True if 'privileges_group_read' in form_dict\
        else False
    topic_dict['group_write'] = True if 'privileges_group_write' in form_dict\
        else False
    return topic_dict

def validate_topic_data(topic_dict):
    if len(topic_dict['topic']) == 0:
        return {
            'message': 'Keskustelualueen nimi ei saa olla tyhjä',
            'response_code': HTTP_BAD_REQUEST}
    if len(topic_dict['topic']) > MAX_TOPIC:
        return {
            'message': 'Keskustelualueen nimi saa olla enintään '\
                + f'{MAX_TOPIC} merkkiä pitkä',
            'response_code': HTTP_BAD_REQUEST}
    if len(topic_dict['description']) == 0:
        return {
            'message': 'Keskustelualueen kuvaus ei saa olla tyhjä',
            'response_code': HTTP_BAD_REQUEST}
    if len(topic_dict['topic']) > MAX_TOPIC_DESCRIPTION:
        return {
            'message': 'Keskustelualueen kuvaus saa olla enintään '\
                + f'{MAX_TOPIC_DESCRIPTION} merkkiä pitkä',
            'response_code': HTTP_BAD_REQUEST}

def delete_topic(topic_id):
    sql_delete_privileges = """
        DELETE FROM topic_privileges WHERE topic_id=:topic_id
    """
    sql_delete_group = """
        DELETE FROM groups WHERE group_name=(
            SELECT topic FROM topics WHERE id=:topic_id)
    """
    sql_delete_topic = """
        DELETE FROM topics WHERE id=:topic_id
    """
    topic_dict = {'topic_id': topic_id}
    db.session.execute(sql_delete_privileges, topic_dict)
    db.session.execute(sql_delete_group, topic_dict)
    db.session.execute(sql_delete_topic, topic_dict)
    db.session.commit()

def set_privileges(topic_dict):
    sql_all = """
        UPDATE topic_privileges
        SET know_priv=:all_know, read_priv=:all_read, write_priv=:all_write
        WHERE topic_id=:topic_id AND group_id=:group_id_ALL
    """
    sql_group = """
        UPDATE topic_privileges
        SET know_priv=:group_know, read_priv=:group_read, write_priv=:group_write
        WHERE topic_id=:topic_id
            AND group_id=(SELECT id FROM groups WHERE group_name=:topic)
    """
    print('SET_PRIVILEGES: ', topic_dict)
    topic_dict['group_id_ALL'] = GROUP_ID__ALL
    db.session.execute(sql_all, topic_dict)
    db.session.execute(sql_group, topic_dict)
    db.session.commit()

def update_topic(topic_dict):
    sql = """
        UPDATE topics SET topic=:topic, description=:description
        WHERE id=:topic_id
    """
    db.session.execute(sql, topic_dict)
    set_privileges(topic_dict)
