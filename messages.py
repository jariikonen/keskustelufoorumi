from db import db

def get_message_threads(topic_id):
    sql = '''
        SELECT id, topic_id, parent_id, writer_id, heading,
            substring(content from 0 for 50), sent_at
        FROM messages
        WHERE topic_id=:topic_id AND parent_id IS NULL
    '''
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
                = latest_message_times[thread.id].strftime("%d.%m.%Y klo %H:%M")
        else:
            latest_message_times[thread.id] = '-'
    return latest_message_times

def get_messages(thread_id):
    result = db.session.execute(
        'SELECT * FROM messages WHERE thread_id=:id',
        {'id': thread_id}
    )
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
    result = db.session.execute(
        'SELECT * FROM messages WHERE id=:id',
        {'id': message_id}
    )
    return result.fetchone()
