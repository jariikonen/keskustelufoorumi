from db import db
import variables

def get_message_threads(topic_id):
    sql = """
        SELECT id, topic_id, refers_to, writer_id, heading,
            substring(content from 0 for 50), sent_at
        FROM messages
        WHERE topic_id=:topic_id AND refers_to IS NULL
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
                = latest_message_times[thread.id].strftime('%d.%m.%Y klo %H:%M')
        else:
            latest_message_times[thread.id] = '-'
    return latest_message_times

def get_messages(thread_id):
    sql = """
        SELECT messages.*, topics.topic, thread.heading as thread,
            users.username as writer
        FROM messages, topics, messages as thread, users
        WHERE messages.thread_id=:id
            AND topics.id=messages.topic_id
            AND thread.id=messages.thread_id
            AND users.id=messages.writer_id
    """
    result = db.session.execute(sql, {'id': thread_id})
    return result.fetchall()

def get_writers(message_list):
    writer_dict = {}
    for message in message_list:
        result = db.session.execute(
            'SELECT username FROM users WHERE id=:id',
            {'id': message.writer_id}
        )
        writer_dict[message.id] = result.fetchone()[0]
    return writer_dict

def get_message(message_id):
    sql = """
        SELECT messages.*, users.username as writer
        FROM messages, users
        WHERE messages.id=:id
            AND users.id=messages.writer_id
    """
    result = db.session.execute(sql,{'id': message_id})
    return result.fetchone()

def get_message_full(message_id):
    sql = """
        SELECT messages.*, topics.topic, thread.heading as thread,
            users.username as writer, referred.heading as referred,
            referred.writer_id as referred_writer_id,
            referred.sent_at as referred_sent_at,
            referred_writer.username as referred_writer_username
        FROM messages, topics, messages as thread, messages as referred, users,
            users as referred_writer
        WHERE messages.id=:id
            AND topics.id=messages.topic_id
            AND thread.id=messages.thread_id
            AND referred.id=messages.refers_to
            AND users.id=messages.writer_id
    """
    result = db.session.execute(sql, {'id': message_id})
    return result.fetchone()

def update_thread_id(message_id, thread_id):
    sql = """
        UPDATE messages SET thread_id=:thread_id WHERE id=:message_id
    """
    result = db.session.execute(
        sql, {'thread_id': thread_id, 'message_id': message_id}
    )

def insert_message(message_dict):
    sql = """
        INSERT INTO messages (topic_id, refers_to, thread_id, writer_id, heading, content)
        VALUES (:topic_id, :refers_to, :thread_id, :writer_id, :heading, :content)
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
    
