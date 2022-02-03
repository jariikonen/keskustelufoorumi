from app import app
from flask import redirect, render_template, request, session
import topics
import messages
import users

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
    writer_list = messages.get_writers(message_list)    # TÄMÄ VOITAISIIN YHDISTÄÄ EDELLISEEN -- TURHA!
    return render_template(
        'thread.html', message_list=message_list, writer_list=writer_list
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        if password1 != password2:
            return render_template('register.html', error='Salasanat eivät olleet samat!')
        success, error = users.register(username, password1)
        if success:
            return redirect('/')
        else:
            return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.login(username, password):
            return redirect('/')
        else:
            return render_template('login.html', error='Väärä tunnus tai salasana!')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')
