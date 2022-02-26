from urllib import response
from app import app
from flask import redirect, render_template, request, session
from constants import *
import topics
import messages
import users
import auth

@app.route('/')
def index():
    return redirect('/topics')

@app.route('/topic')
def topic_root():
    return redirect('/topics')

@app.route('/topics')
def topic_list(error=None):
    user_memberships = session.get('memberships', (3,))
    user_role = session.get('user_role')
    topic_list = topics.get_topics()
    topic_privileges = topics.get_all_topic_privileges()
    secret_topics = topics.get_secret_topics(
        topic_list, topic_privileges, user_memberships, user_role
    )
    thread_nums = topics.get_num_of_threads(topic_list)
    message_nums = topics.get_num_of_messages(topic_list)
    latest_message_times = topics.get_time_of_latest_message(topic_list)
    return render_template(
        'topic-list.html', topic_list=topic_list, secret_topics=secret_topics,
        tpriv=topic_privileges, thread_nums=thread_nums,
        message_nums=message_nums, latest_message_times=latest_message_times,
        error=error
    )

@app.route('/topic/<int:topic_id>')
def topic(topic_id, error=None):
    if topic_id == 0:
        return redirect('/topics')

    topic_row = topics.get_topic(topic_id)
    topic_privileges = auth.has_privilege(topic_id, PRIVILEGE_READ)
    if topic_privileges:
        thread_list = messages.get_message_threads(topic_id)
        message_nums = messages.get_num_of_messages(thread_list)
        latest_message_times = messages.get_time_of_latest_message(thread_list)
        logout_return = f'topic/{topic_id}'
        if not auth.all_has_privilege(topic_id, PRIVILEGE_READ, topic_privileges):
            logout_return = 'topics'
        return render_template(
            'topic.html', topic=topic_row, thread_list=thread_list,
            message_nums=message_nums, latest_message_times=latest_message_times,
            logout_return=logout_return, error=error
        )
    elif 'username' not in session:
        return_url = f'topic/{topic_id}'
        return render_template('login.html', return_url=return_url)

    return topic_list(
        'Sinulla ei ole lukuoikeutta keskustelualueeseen!'
    ), HTTP_FORBIDDEN

@app.route('/thread/<int:thread_id>')
def thread(thread_id, error=None):
    if thread_id == 0:
        return redirect('/topics')

    message_list = messages.get_messages(thread_id)
    if len(message_list) == 0:
        return render_template(
            'error.html', reponse_code=HTTP_NOT_FOUND,
            message='Viestiketjua ei löytynyt'
        ), HTTP_NOT_FOUND
    
    topic_id = message_list[0].topic_id
    topic_privileges = auth.has_privilege(topic_id, PRIVILEGE_READ)
    if not topic_privileges:
        return topic_list(
            'Sinulla ei ole lukuoikeutta keskustelualueeseen!'
        ), HTTP_FORBIDDEN
    logout_return = f'thread/{thread_id}'
    if not auth.all_has_privilege(topic_id, PRIVILEGE_READ, topic_privileges):
        logout_return = 'topics'
    return render_template(
        'thread.html', message_list=message_list, logout_return=logout_return,
        user_id=session.get('user_id'), error=error
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template(
            'register.html', return_url=request.args.get('return_url', '')
        )
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        success, error = users.validate_user_data(username, password1, password2)
        if not success:
            return render_template('register.html', error=error)
        success, error = users.register(username, password1)
        if success:
            return redirect(f"/{request.form.get('return_url')}")
        return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return_url = request.args.get('return_url')
        if not return_url:
            return_url = request.form.get('return_url')
        return render_template('login.html', return_url=return_url)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        return_url = request.args.get('return_url', '')
        if return_url == '':
            return_url = request.form.get('return_url', '')
        if auth.login(username, password):
            return redirect(f'/{return_url}')
        return render_template(
            'login.html', error='Väärä tunnus tai salasana!',
            return_url=return_url
        )

@app.route('/logout')
def logout():
    auth.logout()
    return redirect(f'/{request.args.get("return_url", "")}')

@app.route('/post', methods=['GET'])
def post_get():
    topic_id = request.args.get('topic', 0)
    thread_id = request.args.get('thread', 0)
    reply_to_id = request.args.get('reply', 0)
    if not topic_id:
        return render_template(
            'error.html', response_code=HTTP_BAD_REQUEST,
            message='Pyynnöstä puuttuu keskustelualue'
        ), HTTP_NOT_FOUND

    if 'username' not in session:
        return_url = f'post?topic={topic_id}'
        if thread_id and thread_id != 0:
            return_url += f'&thread={thread_id}&reply={reply_to_id}'
        return render_template('login.html', return_url=return_url)

    topic_row = topics.get_topic(topic_id)
    thread_row = messages.get_message(thread_id)
    reply_row = messages.get_message(reply_to_id)
    topic_privileges = auth.has_privilege(topic_id, PRIVILEGE_WRITE)
    if topic_privileges:
        if thread_id:
            return_url = f'thread/{thread_id}'
        else:
            return_url = f'topic/{topic_id}'
        logout_return = return_url
        if not auth.all_has_privilege(topic_id, PRIVILEGE_READ, topic_privileges):
            logout_return = 'topics'
        return render_template(
            'post.html', return_url=return_url, topic=topic_row,
            thread=thread_row, reply_to=reply_row, logout_return=logout_return
        )
    if thread_id:
        return thread(
            thread_id, 'Sinulla ei ole kirjoitusoikeutta alueella'
        ), HTTP_FORBIDDEN
    return topic(
        topic_id, 'Sinulla ei ole kirjoitusoikeutta alueella'
    ), HTTP_FORBIDDEN

def post_get_with_error_msg(error, return_url, topic_id, thread_id, reply_to_id):
    if 'username' not in session:
        return_url = f'post?topic={topic_id}'
        if thread_id and thread_id != 0:
            return_url += f'&thread={thread_id}&reply={reply_to_id}'
        return render_template('login.html', return_url=return_url)

    topic_row = topics.get_topic(topic_id)
    thread_row = messages.get_message(thread_id)
    reply_row = messages.get_message(reply_to_id)
    return render_template(
        'post.html', error=error, return_url=return_url, topic=topic_row,
        thread=thread_row, reply_to=reply_row
    )

@app.route('/post', methods=['POST'])
def post_post():
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        return post_get_with_error_msg(
            error='Toimenpide ei ole oikeutettu (puuttuva tunniste)!',
            return_url=request.form['return_url'],
            topic_id=request.form.get('topic_id', 0),
            thread_id=request.form.get('thread_id', 0),
            reply_to_id=request.form.get('refers_to', 0)
        )

    message_data = {
        'topic_id': request.form['topic_id'],
        'refers_to': request.form['refers_to'],
        'thread_id': request.form['thread_id'],
        'writer_id': session['user_id'],
        'heading': request.form['heading'],
        'content': request.form['content']
    }
    error = messages.check_message_data(message_data)
    if not error:
        messages.insert_message(message_data)
        return redirect(f'/{request.form["return_url"]}')
    return post_get_with_error_msg(
        error,
        return_url=request.form['return_url'],
        topic_id=request.form.get('topic_id', 0),
        thread_id=request.form.get('thread_id', 0),
        reply_to_id=request.form.get('refers_to', 0)
    )

@app.route('/edit/message/<int:message_id>', methods=['GET'])
def edit_message_get(message_id):
    message_row = messages.get_message(message_id)
    user_id = session.get('user_id')
    if user_id != message_row.writer_id:
        return thread(
            message_row.thread_id,
            'Et voi muokata viestiä, jota et ole kirjoittanut'
        ), HTTP_FORBIDDEN

    referred_row = None
    if message_row.refers_to:
        referred_row = messages.get_message(message_row.refers_to)

    logout_return = f'thread/{message_row.thread_id}'
    if not auth.all_has_privilege(message_row.topic_id, PRIVILEGE_READ):
        logout_return = 'topics'
    return render_template(
        'edit.html', message=message_row, user_id=user_id,
        referred=referred_row, logout_return=logout_return
    )

@app.route('/edit/message/<int:message_id>', methods=['POST'])
def edit_message_post(message_id):
    message_row = messages.get_message_concise(message_id)
    user_id = session.get('user_id')
    if user_id != message_row.writer_id:
        return render_template(
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Et voi muokata viestiä, jota et ole kirjoittanut'
        ), HTTP_FORBIDDEN
    message_data = {
        'id': message_id,
        'heading': request.form['heading'],
        'content': request.form['content']
    }
    messages.update_message(message_data)
    return redirect(f'/thread/{message_row.thread_id}')

@app.route('/delete/message/<int:message_id>', methods=['GET'])
def delete_message_get(message_id):
    message_row = messages.get_message_concise(message_id)
    if not message_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei löytynyt'
        ), HTTP_NOT_FOUND

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if user_id != message_row.writer_id and user_role != USER_ROLE__ADMIN\
            and user_role != USER_ROLE__SUPER:
        return render_template(
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Et voi poistaa viestiä, jota et ole kirjoittanut'
        ), HTTP_FORBIDDEN

    return render_template(
        'confirmation.html', submit_url=f'/delete/message/{message_row.id}',
        question='Haluatko varmaasti poistaa viestin?',
        target_description=f'Viesti: {message_row.heading}',
        submit_button_text='Poista', cancel_url=f'/thread/{message_row.thread_id}'
    )

@app.route('/delete/message/<int:message_id>', methods=['POST'])
def delete_message_post(message_id):
    message_row = messages.get_message_concise(message_id)
    if not message_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei löytynyt'
        ), HTTP_NOT_FOUND

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if user_id != message_row.writer_id and user_role != USER_ROLE__ADMIN\
            and user_role != USER_ROLE__SUPER:
        return render_template(
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Et voi poistaa viestiä, jota et ole kirjoittanut'
        ), HTTP_FORBIDDEN

    error_dict = messages.delete_message(message_row, user_id, user_role)
    if not error_dict:
        if message_row.id == message_row.thread_id:
            return redirect(f'/topic/{message_row.topic_id}')
        return redirect(f'/thread/{message_row.thread_id}')
    return render_template(
        'error.html', message=error_dict['message'],
        response_code=error_dict['response_code']
    ), error_dict['response_code']

@app.route('/restore/message/<int:message_id>', methods=['GET'])
def restore_message_get(message_id):
    message_row = messages.get_message(message_id)
    if not message_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei löytynyt'
        ), HTTP_NOT_FOUND
    if not message_row.deleted:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei ole poistettu'
        ), HTTP_NOT_FOUND

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if user_id != message_row.writer_id and user_role != USER_ROLE__ADMIN\
            and user_role != USER_ROLE__SUPER:
        return render_template(
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Et voi palauttaa viestiä, jota et ole poistanut'
        ), HTTP_FORBIDDEN

    if user_role == USER_ROLE__ADMIN or user_role == USER_ROLE__SUPER\
            and  message_row.writer_id != user_id\
            and (message_row.deleter_role == USER_ROLE__ADMIN\
            or message_row.deleter_role == USER_ROLE__SUPER):
        return render_template(
            'confirmation.html', submit_url=f'/restore/message/{message_row.id}',
            question='Haluatko varmaasti palauttaa viestin?',
            target_description=f'Viesti: {message_row.heading}',
            submit_button_text='Palauta', cancel_url=f'/thread/{message_row.thread_id}'
        )

    logout_return = f'thread/{message_row.thread_id}'
    if not auth.all_has_privilege(message_row.topic_id, PRIVILEGE_READ):
        logout_return = 'topics'
    referred_row = messages.get_message_concise(message_row.refers_to)
    if user_id == message_row.writer_id:
        return render_template(
            'restore.html', message=message_row, logout_return=logout_return,
            referred=referred_row
        )

@app.route('/restore/message/<int:message_id>', methods=['POST'])
def restore_message_post(message_id):
    message_row = messages.get_message_concise(message_id)
    if not message_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei löytynyt'
        ), HTTP_NOT_FOUND
    if not message_row.deleted:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Viestiä ei ole poistettu'
        ), HTTP_NOT_FOUND

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if user_id != message_row.writer_id and user_role != USER_ROLE__ADMIN\
            and user_role != USER_ROLE__SUPER:
        return render_template(
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Et voi palauttaa viestiä, jota et ole poistanut'
        ), HTTP_FORBIDDEN

    if user_role == USER_ROLE__ADMIN or user_role == USER_ROLE__SUPER\
            and  message_row.writer_id != user_id\
            and (message_row.deleter_role == USER_ROLE__ADMIN\
            or message_row.deleter_role == USER_ROLE__SUPER):
        messages.restore_message({'id': message_row.id}, False)
        return redirect(f'/thread/{message_row.thread_id}')

    if user_id == message_row.writer_id:
        message_data = {
            'id': message_id,
            'heading': request.form['heading'],
            'content': request.form['content']
        }
        messages.restore_message(message_data, True)
        return redirect(f'/thread/{message_row.thread_id}')

@app.route('/admin', methods=['GET'])
def admin_get():
    if 'username' not in session:
        return render_template('login.html', return_url='admin')

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat käyttää hallintapaneelia'
        return topic_list(message), response_code
    return render_template('admin.html')

@app.route('/admin', methods=['POST'])
def admin_post():
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return render_template('admin.html', error=error), HTTP_FORBIDDEN

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat käyttää hallintapaneelia'
        return topic_list(message), response_code

    topic_id, error, response_code = topics.insert_topic(
        request.form['topic'],
        request.form['description']
    )
    if error:
        return render_template('admin.html', error=error), response_code
    return redirect(f'/topic/{topic_id}')
