import secrets
from app import app
from flask import redirect, render_template, request, session, url_for
import topics
import messages
import users

@app.route('/')
def index():
    return redirect('/topics')

@app.route('/topic')
def topic_root():
    return redirect('/topics')

@app.route('/topics')
def topic_list():
    topic_list = topics.get_topics()
    thread_nums = topics.get_num_of_threads(topic_list)
    message_nums = topics.get_num_of_messages(topic_list)
    latest_message_times = topics.get_time_of_latest_message(topic_list)
    return render_template(
        'topic-list.html', topic_list=topic_list, thread_nums=thread_nums,
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
    return render_template('thread.html', message_list=message_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        success, error = users.validate_user_data(username, password1, password2)
        if not success:
            return render_template('register.html', error=error)
        success, error = users.register(username, password1)
        if success:
            return redirect('/')
        else:
            return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return_url = request.args.get('return_url', None)
        if not return_url:
            return_url = request.form.get('return_url', None)
        return render_template('login.html', return_url=return_url)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        return_url = request.args.get('return_url', '')
        if return_url == '':
            return_url = request.form.get('return_url', '')
        if users.login(username, password):
            return redirect(f'/{return_url}')
        else:
            return render_template(
                'login.html', error='Väärä tunnus tai salasana!',
                return_url=return_url
            )

@app.route('/logout')
def logout():
    users.logout()
    return redirect(f'/{request.args.get("return_url", "")}')

@app.route('/post', methods=['GET'])
def post_get(error=None, return_url=''):
    topic_id = request.args.get('topic', 0)
    thread_id = request.args.get('thread', 0)
    reply_to_id = request.args.get('reply', 0)
    if not error and 'username' not in session:
        return_url = f'post?topic={topic_id}&thread={thread_id}&reply={reply_to_id}'
        return render_template('login.html', return_url=return_url)

    topic_obj = topics.get_topic(topic_id)
    thread_obj = messages.get_message(thread_id)
    reply_obj = messages.get_message(reply_to_id)
    if error:
        return render_template(
            'post.html', return_url=return_url, topic=topic_obj,
            thread=thread_obj, reply_to=reply_obj
        )    

    return_url = ''
    if thread_id:
        return_url = f'thread/{thread_id}'
    else:
        return_url = f'topic/{topic_id}'
    return render_template(
        'post.html', return_url=return_url, topic=topic_obj,
        thread=thread_obj, reply_to=reply_obj
    )

@app.route('/post', methods=['POST'])
def post_post():
    csrf_token = request.form.get('csrf_token', None)
    if csrf_token != session['csrf_token']:
        return post_get('Toimenpide ei ole oikeutettu (puuttuva tunniste)!')
    
    message_data = {
        'topic_id': request.form['topic_id'],
        'refers_to': request.form['refers_to'],
        'thread_id': request.form['thread_id'],
        'writer_id': session['user_id'],
        'heading': request.form['heading'],
        'content': request.form['content']
    }
    messages.insert_message(message_data)
    return redirect(f'/{request.form.get("return_url", "")}')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
        return render_template('admin.html')
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token', None)
        if csrf_token != session['csrf_token']:
            return post_get('Toimenpide ei ole oikeutettu (puuttuva tunniste)!')
        
        topic_data = {
            'topic': request.form['topic'],
            'description': request.form['description']
        }
        topic_id, error = topics.insert_topic(topic_data)
        if topic_id:
            return redirect(f'/topic/{topic_id}')
        else:
            return render_template('admin.html', error=error)
    
