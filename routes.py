from urllib import response
from app import app
from flask import redirect, render_template, request, session
from constants import *
import topics
import messages
import users
import auth
import url

@app.route('/')
def index():
    return redirect('/topics')

@app.route('/topic')
def topic_root():
    return redirect('/topics')

@app.route('/topics')
def topic_list__both(error=None):
    user_memberships = session.get('memberships', (3,))
    user_role = session.get('user_role')
    topic_list = topics.get_topics_with_privileges()
    secret_topics = topics.get_secret_topics(
        topic_list, user_memberships, user_role)
    thread_nums = topics.get_num_of_threads(topic_list)
    message_nums = topics.get_num_of_messages(topic_list)
    latest_message_times = topics.get_time_of_latest_message(topic_list)
    return render_template(
        'topic-list.html', topic_list=topic_list, secret_topics=secret_topics,
        thread_nums=thread_nums, message_nums=message_nums,
        latest_message_times=latest_message_times, error=error
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

    return topic_list__both(
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
        return topic_list__both(
            'Sinulla ei ole lukuoikeutta keskustelualueeseen!'
        ), HTTP_FORBIDDEN
    logout_return = f'thread/{thread_id}'
    if not auth.all_has_privilege(topic_id, PRIVILEGE_READ, topic_privileges):
        logout_return = 'topics'
    return render_template(
        'thread.html', message_list=message_list, logout_return=logout_return,
        user_id=session.get('user_id'), user_role=session.get('user_role'),
        error=error
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
        error_dict = users.validate_user_data(username, password1, password2)
        if error_dict:
            return render_template(
                'register.html', error=error_dict['message']
            ), error_dict['response_code']
        error_dict = users.register(username, password1)
        if not error_dict:
            return redirect(f"/{request.form.get('return_url')}")
        return render_template(
            'register.html', error=error_dict['message']
        ), error_dict['response_code']

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
            'login.html', error='Väärä tunnus tai salasana',
            return_url=return_url
        )

@app.route('/logout')
def logout():
    auth.logout()
    return redirect(f'/{request.args.get("return_url", "")}')

def post_login(topic_id, thread_id, reply_to_id):
    return_url = f'post?topic={topic_id}'
    if thread_id and thread_id != 0:
        return_url += f'&thread={thread_id}&reply={reply_to_id}'
    return render_template('login.html', return_url=return_url)

def post_return_url(thread_id, topic_id):
    if thread_id:
        return f'thread/{thread_id}'
    return f'topic/{topic_id}'

def post_render_template(
        topic_row, thread_row, reply_row, return_url, logout_return,
        error=None, heading=None, content=None):
    heading_autofocus = True
    content_autofocus = False
    if reply_row and not heading:
        heading = f'VS: {reply_row.heading}'[:MAX_HEADING]
        heading_autofocus = False
        content_autofocus = True
    return render_template(
        'post.html', error=error, return_url=return_url, topic=topic_row,
        thread=thread_row, reply_to=reply_row, logout_return=logout_return,
        heading=heading, content=content, heading_autofocus=heading_autofocus,
        content_autofocus=content_autofocus, max_heading=MAX_HEADING,
        max_content=MAX_CONTENT
    )

def post_check_privilege(
        topic_id:int, thread_id:int, topic_row, thread_row, reply_row,
        error=None, heading=None, content=None):
    topic_privileges = auth.has_privilege(topic_id, PRIVILEGE_WRITE)
    if topic_privileges:
        return_url = post_return_url(thread_id, topic_id)
        logout_return = return_url
        if not auth.all_has_privilege(topic_id, PRIVILEGE_READ, topic_privileges):
            logout_return = 'topics'
        return post_render_template(
            topic_row, thread_row, reply_row, return_url, logout_return,
            error, heading=heading[:MAX_HEADING] if heading else None,
            content=content[:MAX_CONTENT] if content else None
        )
    if thread_id:
        return thread(
            thread_id, 'Sinulla ei ole kirjoitusoikeutta alueella'
        ), HTTP_FORBIDDEN
    return topic(
        topic_id, 'Sinulla ei ole kirjoitusoikeutta alueella'
    ), HTTP_FORBIDDEN

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
        return post_login(topic_id, thread_id, reply_to_id)

    topic_row = topics.get_topic(topic_id)
    thread_row = messages.get_message(thread_id)
    reply_row = messages.get_message(reply_to_id)
    return post_check_privilege(
        topic_id, thread_id, topic_row, thread_row, reply_row
    )

def post_get_with_error(
        error, topic_id, thread_id, reply_to_id, heading, content):
    topic_row = topics.get_topic(topic_id)
    thread_row = messages.get_message(thread_id)
    reply_row = messages.get_message(reply_to_id)
    return post_check_privilege(
        topic_id, thread_id, topic_row, thread_row, reply_row, error,
        heading, content
    )

def post_post_check_requirements(topic_id:int):
    if 'username' not in session:
        return {
            'response_code': HTTP_FORBIDDEN,
            'message': 'Sinun täytyy olla kirjautunut sisään voidaksesi '\
                +'julkaista foorumilla'
        }
    if not auth.has_privilege(topic_id, PRIVILEGE_WRITE):
        return {
            'response_code': HTTP_FORBIDDEN,
            'message': 'Sinulla ei ole kirjoitusoikeutta alueella' 
        }
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        return {
            'response_code': HTTP_FORBIDDEN,
            'message': 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        }

@app.route('/post', methods=['POST'])
def post_post():
    topic_id = None if request.form.get('topic_id') == ''\
        else request.form.get('topic_id')
    thread_id = None if request.form.get('thread_id') == ''\
        else request.form.get('thread_id')
    refers_to = None if request.form.get('refers_to') == ''\
        else request.form.get('refers_to')

    error_dict = post_post_check_requirements(topic_id)
    if error_dict:
        return render_template(
            'error.html', response_code=error_dict['response_code'],
            message=error_dict['message']
        ), error_dict['response_code']

    message_data = {
        'topic_id': topic_id, 'refers_to': refers_to, 'thread_id': thread_id,
        'writer_id': session['user_id'], 'heading': request.form['heading'],
        'content': request.form['content']
    }
    messages.check_refers_to(message_data)
    error = messages.check_message_data(message_data)
    if error:
        return post_get_with_error(
            error, topic_id=topic_id, thread_id=thread_id, reply_to_id=refers_to,
            heading=request.form.get('heading'),
            content=request.form.get('content')
        ), HTTP_BAD_REQUEST
    messages.insert_message(message_data)
    return_url = post_return_url(thread_id, topic_id)
    return redirect(f'/{return_url}')

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
        'edit_message.html', message=message_row, user_id=user_id,
        referred=referred_row, logout_return=logout_return,
        max_heading=MAX_HEADING, max_content=MAX_CONTENT
    )

def edit_message_get_with_error(message_id, error, heading, content):
    message_row = messages.get_message(message_id)
    user_id = session.get('user_id')
    referred_row = None
    if message_row.refers_to:
        referred_row = messages.get_message(message_row.refers_to)
    logout_return = f'thread/{message_row.thread_id}'
    if not auth.all_has_privilege(message_row.topic_id, PRIVILEGE_READ):
        logout_return = 'topics'
    return render_template(
        'edit_message.html', message=message_row, user_id=user_id,
        referred=referred_row, logout_return=logout_return, error=error,
        heading=heading[:MAX_HEADING], content=content[:MAX_CONTENT],
        max_heading=MAX_HEADING, max_content=MAX_CONTENT
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
    error = messages.check_message_data(message_data)
    if error:
        return edit_message_get_with_error(
            message_id, error,
            heading=request.form.get('heading'),
            content=request.form.get('content')
        ), HTTP_BAD_REQUEST
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
        submit_button_text='Poista', cancel_url=f'thread/{message_row.thread_id}'
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
            'error.html', response_code=HTTP_FORBIDDEN,
            message='Viestiä ei ole poistettu'
        ), HTTP_FORBIDDEN

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    is_writer = user_id == message_row.writer_id
    is_admin = user_role == USER_ROLE__ADMIN or user_role == USER_ROLE__SUPER
    deleted_by_writer = message_row.deleter_role == USER_ROLE__USER
    if is_admin and not is_writer and not deleted_by_writer:
        return render_template(
            'confirmation.html',
            submit_url=f'/restore/message/{message_row.id}',
            question='Haluatko varmaasti palauttaa viestin?',
            target_description=f'Viesti: {message_row.heading}',
            submit_button_text='Palauta',
            cancel_url=f'thread/{message_row.thread_id}'
        )
    if (is_writer and not is_admin and deleted_by_writer)\
            or (is_writer and is_admin):
        logout_return = f'thread/{message_row.thread_id}'
        if not auth.all_has_privilege(message_row.topic_id, PRIVILEGE_READ):
            logout_return = 'topics'
        referred_row = messages.get_message_concise(message_row.refers_to)
        return render_template(
            'restore.html', message=message_row, logout_return=logout_return,
            referred=referred_row, max_heading=MAX_HEADING,
            max_content=MAX_CONTENT
        )
    error = 'Et voi palauttaa viestiä, koska se on poistettu kirjoittajan '\
        +'itsensä toimesta'
    if is_writer:
        error = 'Et voi palauttaa viestiä, koska se on poistettu ylläpidon '\
            +'toimesta'
    return thread(message_row.thread_id, error), HTTP_FORBIDDEN

def restore_message_get_with_error(message_id, error, heading, content):
    message_row = messages.get_message(message_id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    is_writer = user_id == message_row.writer_id
    is_admin = user_role == USER_ROLE__ADMIN or user_role == USER_ROLE__SUPER
    deleted_by_writer = message_row.deleter_role == USER_ROLE__USER
    if (is_writer and not is_admin and deleted_by_writer)\
            or (is_writer and is_admin):
        logout_return = f'thread/{message_row.thread_id}'
        if not auth.all_has_privilege(message_row.topic_id, PRIVILEGE_READ):
            logout_return = 'topics'
        referred_row = messages.get_message_concise(message_row.refers_to)
        return render_template(
            'restore.html', message=message_row, logout_return=logout_return,
            referred=referred_row, error=error, heading=heading[:MAX_HEADING],
            content=content[:MAX_CONTENT], max_heading=MAX_HEADING,
            max_content=MAX_CONTENT
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
    is_writer = user_id == message_row.writer_id
    is_admin = user_role == USER_ROLE__ADMIN or user_role == USER_ROLE__SUPER
    deleted_by_writer = message_row.deleter_role == USER_ROLE__USER
    if is_admin and not is_writer and not deleted_by_writer:
        messages.restore_message({'id': message_row.id}, False)
        return redirect(f'/thread/{message_row.thread_id}')
    if (is_writer and not is_admin and deleted_by_writer)\
            or (is_writer and is_admin):
        message_data = {
            'id': message_id,
            'heading': request.form['heading'],
            'content': request.form['content']
        }
        error = messages.check_message_data(message_data)
        if error:
            return restore_message_get_with_error(
                message_id, error,
                heading=request.form.get('heading'),
                content=request.form.get('content')
            ), HTTP_BAD_REQUEST
        messages.restore_message(message_data, True)
        return redirect(f'/thread/{message_row.thread_id}')
    error = 'Et voi palauttaa viestiä, koska se on poistettu kirjoittajan '\
        +'itsensä toimesta'
    if is_writer:
        error = 'Et voi palauttaa viestiä, koska se on poistettu ylläpidon '\
            +'toimesta'
    return render_template(
        'error.html', response_code=HTTP_FORBIDDEN, message=error
    ), HTTP_FORBIDDEN

@app.route('/user/<int:user_id>', methods=['GET'])
def user__get(user_id, error=None):
    alert_class = request.args.get('alert_class')
    alert_message = request.args.get('alert_message')
    return_url = request.args.get('return_url')
    current_user_data = users.get_current_user_data(target_id=user_id)

    target_row = users.get_user_data(user_id)
    if not target_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Käyttäjää ei löytynyt'
        ), HTTP_NOT_FOUND
    target_user_data = users.get_target_user_data(target_row)

    group_str = None
    if target_row and (current_user_data['is_target']\
            or current_user_data['is_admin']):
        group_str = users.get_user_groups(user_id)

    if target_row:
        return render_template(
            'user.html', target=target_row, group_str=group_str,
            current_data=current_user_data,
            target_data=target_user_data,
            alert_class=alert_class, alert_message=alert_message,
            error=error, return_url=return_url
        )
    return render_template(
        'error.html', response_code=HTTP_NOT_FOUND,
        message='Käyttäjää ei löytynyt'
    ), HTTP_NOT_FOUND

@app.route('/edit/user/<int:user_id>', methods=['GET'])
def edit_user__get(user_id, error=None):
    return_url = request.args.get('return_url')
    current_user_data = users.get_current_user_data(user_id)
    only_super = True
    if current_user_data['is_super']:
        other_supers = users.count_other_super(user_id)
        only_super = False if other_supers > 0 else True

    target_row = users.get_user_data(user_id)
    if not target_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Käyttäjää ei löytynyt'
        ), HTTP_NOT_FOUND
    target_user_data = users.get_target_user_data(target_row)

    return render_template(
        'edit_user.html', target=target_row, current_data=current_user_data,
        target_data=target_user_data, only_super=only_super, error=error,
        max_username=MAX_USERNAME, max_password=MAX_PASSWORD,
        return_url=return_url)

@app.route('/edit/user/<int:user_id>', methods=['POST'])
def edit_user_post(user_id):
    if request.form['csrf_token'] != session['csrf_token']:
        return user__get(
            user_id, 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        ), HTTP_FORBIDDEN

    if not auth.check_password(
            session['user_id'], request.form['requester_password']):
        return edit_user__get(user_id, 'Väärä salasana'), HTTP_FORBIDDEN

    current_user_data = users.get_current_user_data(target_id=user_id)
    target_row = users.get_user_data(user_id)
    target_user_data = users.get_target_user_data(target_row)
    changing_elements_dict = users.find_changing_elements__edit_user(
        target_user_data, request.form)
    error_dict = auth.is_authorized__edit_user(
        current_user_data, target_user_data, changing_elements_dict,
        request.form)
    if error_dict:
        return user__get(
            user_id, error_dict['message']), error_dict['response_code']
    
    error_dict = users.validate_user_data__edit_user(
        changing_elements_dict, request.form)
    if error_dict:
        return user__get(
            user_id, error_dict['message']), error_dict['response_code']

    error_dict = None
    if changing_elements_dict['password']:
        error_dict = users.update_user_data_all(
            user_id, request.form['username'], request.form['role'],
            request.form['new_password1'])
    else:
        error_dict = users.update_username_and_role(
            user_id, request.form['username'], request.form['role'])
    if error_dict:
        return render_template(
            'error.html', message=error_dict['message'],
            response_code=error_dict['response_code']
        ), error_dict['response_code']

    if changing_elements_dict['username'] and current_user_data['is_target']:
        session['username'] = request.form['username']

    message = users.get_success_message__edit_user(
        changing_elements_dict, request.form)
    return redirect(
        f'/user/{user_id}?alert_class=success&'\
            + f'alert_message={url.encode(message)}')

@app.route('/delete/user/<int:user_id>', methods=['GET'])
def delete_user__get(user_id):
    user_row = users.get_user_data(user_id)
    if not user_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Käyttäjää ei löytynyt'
        ), HTTP_NOT_FOUND

    return_url = request.args.get('return_url')
    cancel_url = return_url if return_url else f'user/{user_id}'
    return render_template(
        'confirmation.html', submit_url=f'/delete/user/{user_id}',
        question='Haluatko varmaasti poistaa käyttäjätilin?',
        target_description=f'Käyttäjätili: {user_row.username}',
        submit_button_text='Poista', cancel_url=cancel_url
    )

@app.route('/delete/user/<int:user_id>', methods=['POST'])
def delete_user__post(user_id):
    if request.form['csrf_token'] != session['csrf_token']:
        return user__get(
            user_id, 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        ), HTTP_FORBIDDEN

    current_user_data = users.get_current_user_data(target_id=user_id)
    only_super = True
    if current_user_data['is_super']:
        other_supers = users.count_other_super(user_id)
        only_super = False if other_supers > 0 else True
    target_row = users.get_user_data(user_id)
    target_user_data = users.get_target_user_data(target_row)
    if not current_user_data['is_target']\
            and not current_user_data['is_admin']:
        return user__get(
            user_id, 'Tavallinen käyttäjä voi poistaa vain oman tilinsä'
        ), HTTP_FORBIDDEN
    if not current_user_data['is_target'] and current_user_data['is_admin']\
            and not current_user_data['is_super']\
            and target_user_data['role_super']:
        return user__get(
            user_id, 'Vain pääkäyttäjä voi poistaa pääkäyttäjätilejä'
        ), HTTP_FORBIDDEN
    if target_user_data['role_super'] and only_super:
        return user__get(
            user_id, 'Et voi poistaa tiliäsi, koska olet järjestelmän ainoa '\
                'pääkäyttäjä'
        ), HTTP_FORBIDDEN

    auth.logout()
    users.delete_user(user_id)
    message = f'Käyttäjätili {target_row.username} poistettu'
    return redirect(
        f'/user/{user_id}?alert_class=success&'\
            + f'alert_message={url.encode(message)}')

@app.route('/admin', methods=['GET'])
def admin_get():
    return redirect('/admin/topics')

@app.route('/admin/topics', methods=['GET'])
def admin_topics__get(error=None, topic_dict=None):
    alert_message = request.args.get('alert_message')
    alert_class = request.args.get('alert_class')
    if 'username' not in session:
        return render_template('login.html', return_url='admin')

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat käyttää '\
            + 'hallintapaneelia'
        return topic_list__both(message), response_code

    topic_list = topics.get_topics_with_privileges()
    return_url = url.encode('admin/topics#form')
    return render_template(
        'admin_topics.html', topic_list=topic_list, error=error,
        topic_dict=topic_dict, alert_message=alert_message,
        alert_class=alert_class, return_url=return_url)

@app.route('/new/topic', methods=['POST'])
def new_topic__post():
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return admin_topics__get(error), HTTP_FORBIDDEN

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        error = 'Vain ylläpitäjät ja pääkäyttäjät voivat lisätä '\
            + 'keskustelualueita'
        return topic_list__both(error), HTTP_FORBIDDEN

    topic_dict = topics.form_topic_dict(request.form)
    error_dict = topics.validate_topic_data(topic_dict)
    if error_dict:
        return admin_topics__get(
            error_dict['message'], topic_dict), error_dict['response_code']

    error_dict = topics.new_topic(topic_dict)
    if error_dict:
        return admin_topics__get(
            error_dict['message'], topic_dict), error_dict['response_code']

    message = url.encode("Keskustelualueen lisääminen onnistui")
    return redirect(
        f'/admin/topics?alert_message={message}&alert_class=success')

@app.route('/set_privileges/topic/<int:topic_id>', methods=['POST'])
def set_privileges_topic__post(topic_id):
    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        message = 'Vain ylläpitäjät ja pääkäyttäjät voivat muokata '\
            + 'keskustelualueita'
        return render_template(
            'error.html', HTTP_FORBIDDEN, message=message), HTTP_FORBIDDEN

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return admin_topics__get(error), HTTP_FORBIDDEN

    topic_row = topics.get_topic(topic_id)
    if not topic_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Keskustelualuetta ei löytynyt'), HTTP_NOT_FOUND

    topic_dict = topics.form_topic_dict(request.form, topic_id)
    topics.set_privileges(topic_dict)
    message = url.encode('Käyttöoikeuksien muuttaminen onnistui')
    return redirect(
        f'/admin/topics?alert_message={message}&alert_class=success')

@app.route('/edit/topic/<int:topic_id>', methods=['GET'])
def edit_topic__get(topic_id, error=None, topic_dict=None):
    if 'username' not in session:
        return render_template('login.html', return_url='admin')

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat muokata '\
            + 'keskustelualueita'
        return topic_list__both(message), response_code

    topic_row = topics.get_topic(topic_id)
    if not topic_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Keskustelualuetta ei löytynyt'), HTTP_NOT_FOUND

    return_url = request.args.get('return_url', '')
    topic_row = topics.get_topic_with_privileges(topic_id)
    return render_template(
        'edit_topic.html', topic=topic_row, return_url=return_url,
        error=error, topic_dict=topic_dict)

@app.route('/edit/topic/<int:topic_id>', methods=['POST'])
def edit_topic__post(topic_id):
    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat muokata '\
            + 'keskustelualueita'
        return topic_list__both(message), response_code

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return admin_topics__get(error), HTTP_FORBIDDEN

    topic_row = topics.get_topic(topic_id)
    if not topic_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Keskustelualuetta ei löytynyt'), HTTP_NOT_FOUND

    topic_dict = topics.form_topic_dict(request.form, topic_id)
    error_dict = topics.validate_topic_data(topic_dict)
    if error_dict:
        return edit_topic__get(
            topic_id, error_dict['message'], topic_dict
        ), error_dict['response_code']

    topics.update_topic(topic_dict)
    message = url.encode('Keskustelualueen tietojen muuttaminen onnistui')
    return redirect(
        f'/admin/topics?alert_message={message}&alert_class=success')

@app.route('/delete/topic/<int:topic_id>', methods=['GET'])
def delete_topic__get(topic_id):
    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        message = 'Vain ylläpitäjät ja pääkäyttäjät voivat poistaa '\
            + 'keskustelualueita'
        return render_template(
            'error.html', HTTP_FORBIDDEN, message=message), HTTP_FORBIDDEN

    topic_row = topics.get_topic(topic_id)
    if not topic_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Keskustelualuetta ei löytynyt'), HTTP_NOT_FOUND

    return render_template(
        'confirmation.html', submit_url=f'/delete/topic/{topic_id}',
        question='Haluatko varmaasti poistaa keskustelualueen?',
        target_description=f'Keskustelualue: {topic_row.topic}',
        submit_button_text='Poista', cancel_url=f'admin/topics#form{topic_id}'
    )

@app.route('/delete/topic/<int:topic_id>', methods=['POST'])
def delete_topic__post(topic_id):
    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        message = 'Vain ylläpitäjät ja pääkäyttäjät voivat poistaa '\
            + 'keskustelualueita'
        return render_template(
            'error.html', HTTP_FORBIDDEN, message=message), HTTP_FORBIDDEN

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return admin_topics__get(error), HTTP_FORBIDDEN

    topic_row = topics.get_topic(topic_id)
    if not topic_row:
        return render_template(
            'error.html', response_code=HTTP_NOT_FOUND,
            message='Keskustelualuetta ei löytynyt'), HTTP_NOT_FOUND

    topics.delete_topic(topic_id)
    message = url.encode(f"Keskustelualue '{topic_row.topic}' poistettu")
    return redirect(
        f'/admin/topics?alert_message={message}&alert_class=success')

@app.route('/admin/users', methods=['GET'])
def admin_users__get(error=None):
    alert_message = request.args.get('alert_message')
    alert_class = request.args.get('alert_class')
    if 'username' not in session:
        return render_template('login.html', return_url='admin')

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat käyttää '\
            + 'hallintapaneelia'
        return topic_list__both(message), response_code

    user_list = users.get_user_list()
    group_list = users.get_group_list()
    return_url = url.encode('admin/users#user')
    return render_template(
        'admin_users.html', user_list=user_list, group_list=group_list,
        alert_message=alert_message, alert_class=alert_class, error=error,
        return_url=return_url)

@app.route('/group_add', methods=['POST'])
def group_add__post():
    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat lisätä '\
            + 'käyttäjiä ryhmiin'
        return topic_list__both(message), response_code

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session['csrf_token']:
        error = 'Toimenpide ei ole oikeutettu (puuttuva tunniste)'
        return admin_users__get(error), HTTP_FORBIDDEN

    user_list = request.form.getlist('user')
    group_id = request.form.get('group')
    error_dict = users.group_add(user_list, group_id)
    if error_dict:
        error = f'Lisääminen ei onnistunut: {error_dict["message"]}'
        return admin_users__get(error), HTTP_FORBIDDEN
    message = url.encode(
        f'Käyttäjien {user_list} lisääminen ryhmään {group_id} onnistui')
    return redirect(
        f'/admin/users?alert_message={message}&alert_class=success')

@app.route('/admin/deletions', methods=['GET'])
def admin_deletions__get():
    if 'username' not in session:
        return render_template('login.html', return_url='admin')

    user_role = session.get('user_role')
    if user_role != USER_ROLE__ADMIN and user_role != USER_ROLE__SUPER:
        response_code = HTTP_FORBIDDEN
        message = 'Vain ylläpitäjät ja pääkäyttäjät saavat käyttää '\
            + 'hallintapaneelia'
        return topic_list__both(message), response_code

    return render_template('admin_deletions.html')
