from app import app
from flask import render_template, request
import topics
import messages

@app.route('/')
def index():
    topic_list = topics.get_topics()
    thread_nums = topics.get_num_of_threads(topic_list)
    message_nums = topics.get_num_of_messages(topic_list)
    latest_message_times = topics.get_time_of_latest_message(topic_list)
    return render_template(
        'index.html', topic_list=topic_list, thread_nums=thread_nums,
        message_nums=message_nums, latest_message_times=latest_message_times
    )

@app.route('/topic/<int:topic_id>')
def topic(topic_id):
    topic_obj = topics.get_topic(topic_id)
    thread_list = messages.get_message_threads(topic_id)
    message_nums = messages.get_num_of_messages(thread_list)
    latest_message_times = messages.get_time_of_latest_message(thread_list)
    return render_template(
        'topic.html', topic=topic_obj, thread_list=thread_list,
        message_nums=message_nums, latest_message_times=latest_message_times
    )

@app.route('/thread/<int:thread_id>')
def thread(thread_id):
    message_list = messages.get_messages(thread_id)
    writer_list = messages.get_writers(message_list)
    return render_template(
        'thread.html', message_list=message_list, writer_list=writer_list
    )
