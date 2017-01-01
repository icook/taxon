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
from flask.ext.login import login_required, logout_user, login_user, current_user, abort
from itertools import chain
from itsdangerous import URLSafeSerializer, BadData

from . import root, lm, oauth, cfg, log, tasks, lib


main = Blueprint('main', __name__)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, current_app.config['assets_address'][1:]),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/register", methods=['GET', 'POST'])
def register():
    errors = ['test']
    if request.method == 'POST':
        pass
    return render_template('register.html', errors=errors)


@main.route("/")
def home():
    return render_template('home.html')
