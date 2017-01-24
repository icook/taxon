import re
import os
import time
import rethinkdb
import xxhash

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, flash, session, current_app, jsonify)
from flask_login import login_required, logout_user, login_user, current_user

from . import root, lm, log, tasks, lib, db, crypt, redis_store
from .common_pass import common_pass


main = Blueprint('main', __name__)

url_regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class User:
    def __init__(self, username, active=True, authenticated=True, **kwargs):
        self.__dict__.update(**kwargs)
        self.username = username
        self.active = active
        self.authenticated = authenticated

    def is_authenticated(self):
        return self.authenticated

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return self.authenticated

    def get_id(self):
        return self.username


@lm.user_loader
def load_user(username):
    res = rethinkdb.table("users").get(username).run(db.conn)
    if res is not None:
        return User(**res)
    return None


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@main.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    errors = []
    if request.method == 'POST':
        url = request.values.get('url')
        tags = [request.values.get('tag' + str(i), '').strip().lower() for i in range(10)]
        tags = [t for t in tags if t]

        if not url_regex.match(url):
            errors.append('Invalid URL provided')

        if not errors:
            post_id = xxhash.xxh64(url).hexdigest()
            dat = {'tags': tags,
                   'url': url,
                   'id': post_id,
                   'poster': current_user.username,
                   'posted_at': time.time()}
            rethinkdb.table("posts").insert(dat).run(db.conn)
            for tag in tags:
                lib.vote(post_id, tag, current_user.username, True)

            flash("Post posted!", "success")
            return redirect(url_for('main.home'))

    return render_template('post.html', errors=errors)


@main.route("/login", methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        username = request.values.get('username', '')
        password = request.values.get('password', '')
        res = rethinkdb.table("users").get(username).run(db.conn)
        if res is None or crypt.check(res['password'], password) is False:
            errors.append('Invalid username or password')

        if not errors:
            login_user(User(**res))
            return redirect(url_for('main.home'))

    return render_template('login.html', errors=errors)


@main.route("/register", methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        username = request.values.get('username', '')
        password1 = request.values.get('password', '')
        password2 = request.values.get('password2', '')
        if password1 != password2:
            errors.append('Passwords must match')
        if len(password1) < 8:
            errors.append('Passwords must be at least 8 characters')
        if password1 in common_pass:
            errors.append('Passwords is too easily guessed, pick something different')
        res = rethinkdb.table("users").get(username).run(db.conn)
        if res is not None:
            errors.append('Username is already taken')

        if not errors:
            dat = {'username': username, 'password': crypt.encode(password1), 'reg_date': time.time(), 'subscriptions': default_tags}
            res = rethinkdb.table("users").insert(dat).run(db.conn)
            flash("Thanks for registering, you're now logged in!", "success")
            login_user(User(**dat))
            return redirect(url_for('main.home'))

    return render_template('register.html', errors=errors)


default_tags = ['video', 'image', 'gif', 'tech', 'movies', 'games', 'funny', 'programming', 'fitness']


@main.route("/")
def home():
    tag_scores = {}
    subs = current_user.subscriptions if current_user.is_authenticated else default_tags

    for tag in subs:
        res = redis_store.zrange(tag, 0, 100, withscores=True)
        res = [(b[0].decode('utf8'), b[1]) for b in res]
        tag_scores[tag] = res

    subs_dict = {t: True for t in subs}
    return render_template('home.html', tag_scores=tag_scores, subscriptions=subs_dict)
