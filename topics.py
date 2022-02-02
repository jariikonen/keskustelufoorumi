from db import db

def get_topics(restricted=False):
    result = db.session.execute(
        'SELECT * FROM topics WHERE restricted=:restricted',
        {'restricted': restricted}
    )
    return result.fetchall()

def get_num_of_threads(topics):
    thread_nums = {}
    for topic in topics:
        result = db.session.execute(
            'SELECT COUNT(*) FROM messages WHERE parent_id IS NULL AND topic_id=:id',
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
                = latest_message_times[topic.id].strftime("%d.%m.%Y klo %H:%M")
        else:
            latest_message_times[topic.id] = '-'
    return latest_message_times
