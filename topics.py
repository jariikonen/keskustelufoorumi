from sqlalchemy.exc import IntegrityError
from db import db
from constants import *

def get_topics():
    result = db.session.execute('SELECT * FROM topics ORDER BY id')
    return result.fetchall()

def get_topic(topic_id):
    result = db.session.execute(
        'SELECT * FROM topics WHERE id=:topic_id',
        {'topic_id': topic_id}
    )
    return result.fetchone()

# Used by get_all_topic_privileges() and get_topic_privileges()
def get_privilege_dict(row_list):
    privilege_dict = {}
    for row in row_list:
        if row.topic_id not in privilege_dict.keys():
            privilege_dict[row.topic_id] = {row.group_id: {}}
        else:
            privilege_dict[row.topic_id][row.group_id] = {}
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_KNOW] = row.know_priv
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_READ] = row.read_priv
        privilege_dict[row.topic_id][row.group_id][PRIVILEGE_WRITE] = row.write_priv
    return privilege_dict

def get_all_topic_privileges():
    sql = """
        SELECT topics.id as topic_id, tp.group_id, tp.know_priv, tp.read_priv, tp.write_priv
        FROM topic_privileges as tp, topics, groups
        WHERE topics.id=tp.topic_id
            AND groups.id=tp.group_id
        ORDER BY topic_id
    """
    row_list = db.session.execute(sql).fetchall()
    return get_privilege_dict(row_list)

def get_topic_privileges(topic_id):
    sql = """
        SELECT topics.id as topic_id, tp.group_id, tp.know_priv, tp.read_priv, tp.write_priv
        FROM topic_privileges as tp, topics, groups
        WHERE tp.topic_id=topics.id
            AND groups.id=tp.group_id
            AND topics.id=:topic_id
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

def insert_topic(topic, description):
    sql1 = """
        INSERT INTO topics (topic, description)
        VALUES (:topic, :description)
        RETURNING id
    """
    sql2 = """
        INSERT INTO groups (group_name)
        VALUES (:topic)
        RETURNING id
    """
    sql3 = f"""
        INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
        VALUES ({GROUP_ID__ALL}, :topic_id, :know_priv, :read_priv, :write_priv);
    """
    sql4 = f"""
        INSERT INTO topic_privileges (group_id, topic_id, know_priv, read_priv, write_priv)
        VALUES (:group_id, :topic_id, :know_priv, :read_priv, :write_priv);
    """
    try:
        topic_id = db.session.execute(sql1, topic_dict).fetchone()[0]
        group_id = db.session.execute(sql2, topic_dict).fetchone()[0]

    except IntegrityError:
        return False, 'Aihealue on jo olemassa', HTTP_FORBIDDEN
    db.session.commit()
    return topic_id, '', None
