import decimal
import os
import sqlalchemy
import uuid
import datetime
import time
import jwt
import random

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, flash, session, current_app, jsonify)
from flask_login import login_required, logout_user, login_user, current_user, abort
from itertools import chain
from itsdangerous import URLSafeSerializer, BadData

from . import root, lm, oauth, cfg, log, tasks, lib
from .common_pass import common_pass


main = Blueprint('main', __name__)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/register", methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        username = request.values.get('username', '')
        password1 = request.values.get('password', '')
        password2 = request.values.get('password2', '')
        log.info(password1)
        if password1 != password2:
            errors.append('Passwords must match')
        if len(password1) < 8:
            errors.append('Passwords must be at least 8 characters')
        if password1 in common_pass:
            errors.append('Passwords is too easily guessed, pick something different')
    return render_template('register.html', errors=errors)


@main.route("/")
def home():
    return render_template('home.html')
