from app import app
from flask import render_template
import topics

@app.route("/")
def index():
    topic_list = topics.get_topics()
    thread_nums = topics.get_num_of_threads(topic_list)
    message_nums = topics.get_num_of_messages(topic_list)
    latest_message_times = topics.get_time_of_latest_message(topic_list)
    return render_template(
        "index.html", topic_list=topic_list, thread_nums=thread_nums,
        message_nums=message_nums, latest_message_times=latest_message_times
    )
