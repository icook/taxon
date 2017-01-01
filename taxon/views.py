import decimal
import os
import sqlalchemy
import uuid
import datetime
import time
import jwt
import random
import rethinkdb

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, flash, session, current_app, jsonify)
from flask_login import login_required, logout_user, login_user, current_user, abort
from itertools import chain
from itsdangerous import URLSafeSerializer, BadData

from . import root, lm, oauth, cfg, log, tasks, lib, db, crypt
from .common_pass import common_pass


main = Blueprint('main', __name__)


class User:
    def __init__(self, username, active=True, authenticated=True, **kawargs):
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
            dat = {'username': username, 'password': crypt.encode(password1)}
            res = rethinkdb.table("users").insert(dat).run(db.conn)


    return render_template('register.html', errors=errors)


@main.route("/")
def home():
    return render_template('home.html')
