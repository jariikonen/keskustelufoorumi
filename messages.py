from sqlalchemy.exc import IntegrityError
from db import db
from constants import *
import variables

def get_message_threads(topic_id):
    sql = """
        SELECT M.id, M.topic_id, M.refers_to, M.writer_id, M.heading,
            SUBSTRING(M.content from 0 for 50) AS sample, M.sent_at,
            COUNT(D.message_id) AS deleted
        FROM messages M LEFT JOIN pending_message_deletions D
            ON D.message_id=M.id
        WHERE M.topic_id=:topic_id AND M.refers_to IS NULL
        GROUP BY M.id
        ORDER BY M.id ASC
    """
    result = db.session.execute(sql, {'topic_id': topic_id})
    return result.fetchall()

def get_num_of_messages(threads):
    message_nums = {}
    for thread in threads:
        result = db.session.execute(
            'SELECT COUNT(*) FROM messages WHERE thread_id=:id',
            {'id': thread.id}
        )
        message_nums[thread.id] = result.fetchone()[0]
    return message_nums

def get_time_of_latest_message(threads):
    latest_message_times = {}
    for thread in threads:
        result = db.session.execute(
            'SELECT MAX(sent_at) FROM messages WHERE thread_id=:id',
            {'id': thread.id}
        )
        latest_message_times[thread.id] = result.fetchone()[0]
        if latest_message_times[thread.id]:
            latest_message_times[thread.id]\
                = latest_message_times[thread.id].strftime(
                    '%d.%m.%Y klo %H:%M'
                )
        else:
            latest_message_times[thread.id] = '-'
    return latest_message_times

def get_messages(thread_id):
    sql = """
        SELECT M.id, M.topic_id, M.refers_to, M.thread_id, M.writer_id,
            M.heading, M.content, M.sent_at, T.topic, THREAD.heading as thread,
            U.username as writer, COUNT(D.message_id) as deleted
        FROM messages M LEFT JOIN pending_message_deletions D
            ON M.id=D.message_id, topics T, messages THREAD, users U
        WHERE M.thread_id=:id
            AND T.id=M.topic_id
            AND THREAD.id=M.thread_id
            AND U.id=M.writer_id
        GROUP BY M.id, T.id, thread, U.username
        ORDER BY M.sent_at
    """
    result = db.session.execute(sql, {'id': thread_id})
    return result.fetchall()

def get_message(message_id):
    sql = """
        SELECT M.id, M.topic_id, M.refers_to, M.thread_id, M.writer_id,
            M.heading, M.content, M.sent_at, U.username AS writer,
            T.topic as topic, THREAD.heading AS thread,
            COUNT(D.message_id) AS deleted
        FROM messages M LEFT JOIN pending_message_deletions D
            ON M.id=D.message_id, topics T, messages as THREAD, users U
        WHERE M.id=:id
            AND U.id=M.writer_id
            AND T.id=M.topic_id
            AND THREAD.id=M.thread_id
        GROUP BY M.id, T.id, thread, U.username
    """
    result = db.session.execute(sql, {'id': message_id})
    return result.fetchone()

def get_message_concise(message_id):
    sql = """
        SELECT M.id, M.topic_id, M.refers_to, M.thread_id, M.writer_id,
            M.heading, M.content, M.sent_at, COUNT(D.message_id) AS deleted
        FROM messages M LEFT JOIN pending_message_deletions D
            ON M.id=D.message_id
        WHERE M.id=:id
        GROUP BY M.id
    """
    result = db.session.execute(sql, {'id': message_id})
    return result.fetchone()

def check_message_data(message_data):
    if message_data['heading'] == '':
        return 'Otsikko ei saa olla tyhjä!'
    if message_data['content'] == '':
        return 'Viestin sisältö ei saa olla tyhjä'
    if message_data['refers_to'] == '':
        message_data['refers_to'] = message_data['thread_id']
    return None

def update_thread_id(message_id, thread_id):
    sql = """
        UPDATE messages SET thread_id=:thread_id WHERE id=:message_id
    """
    result = db.session.execute(
        sql, {'thread_id': thread_id, 'message_id': message_id}
    )

def insert_message(message_dict):
    sql = """
        INSERT INTO messages (
            topic_id, refers_to, thread_id, writer_id, heading, content
        )
        VALUES (
            :topic_id, :refers_to, :thread_id, :writer_id, :heading, :content
        )
        RETURNING id
    """
    message_dict = variables.set_empty_to_none(message_dict)
    result = db.session.execute(sql, message_dict)
    message_id = result.fetchone()[0]
    if not message_dict['thread_id']:
        if message_dict['refers_to']:
            update_thread_id(message_id, message_dict['refers_to'])
        else:
            update_thread_id(message_id, message_id)
    db.session.commit()

def update_message(message_dict):
    sql = """
        UPDATE messages SET heading=:heading, content=:content WHERE id=:id
    """
    db.session.execute(sql, message_dict)
    db.session.commit()

def clear_message_content(message_id):
    sql = 'UPDATE messages SET heading=NULL, content=NULL WHERE id=:id'
    db.session.execute(sql, {'id': message_id})

def create_pending_delete(message_row, user_id):
    sql = """
        INSERT INTO pending_message_deletions (message_id, deleted_by)
        VALUES (:message_id, :user_id)
    """
    try:
        db.session.execute(
            'INSERT INTO pending_message_deletions (message_id, deleted_by) VALUES (:message_id, :user_id)',
            {'message_id': message_row.id, 'user_id': user_id}
        )
    except IntegrityError:
        return {
            'message': 'Viesti on jo poistettu',
            'response_code': HTTP_NOT_FOUND
        }

    if user_id == message_row.writer_id:
        clear_message_content(message_row.id)

    db.session.commit()

def delete_message(message_row, user_id, user_role):
    if user_id != message_row.writer_id:
        return create_pending_delete(message_row, user_id)

    sql = 'DELETE FROM messages WHERE id=:message_id'
    try:
        db.session.execute(sql, {'message_id': message_row.id})
    except IntegrityError:
        db.session.rollback()
        return create_pending_delete(message_row, user_id)
    db.session.commit()

def delete_thread(message_row, user_id, user_role, force):
    if user_id == message_row.writer_id\
            or (user_role == USER_ROLE__SUPER and force):
        db.session.execute(
            'DELETE FROM messages WHERE thread_id=:thread_id',
            {'thread_id': message_row.thread_id}
        )
