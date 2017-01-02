import subprocess
import logging
import os
import yaml
import sys
import inspect
import paypal as paypal_lib
import paypalrestsdk
import cryptacular.bcrypt

from flask import Flask, render_template, abort, request, current_app
from flask_login import LoginManager, current_user
from flask_oauthlib.client import OAuth
from flask_rethinkdb import RethinkDB
from flask_redis import FlaskRedis
from celery import Celery
from jinja2 import FileSystemLoader
from werkzeug.local import LocalProxy
from werkzeug.contrib.fixers import ProxyFix

import taxon.filters as filters

root = os.path.abspath(os.path.dirname(__file__) + '/../')
lm = LoginManager()
db = RethinkDB()
oauth = OAuth()
redis_store = FlaskRedis()

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
cfg = LocalProxy(
    lambda: getattr(current_app, 'config', None))
log = LocalProxy(
    lambda: getattr(current_app, 'logger', None))

# Load our application config. Ideally would use env vars, etc
config_path = os.environ.get('TAXON_CONFIG', 'config.yml')
if not config_path.startswith('/'):
    config_path = os.path.join(root, config_path)
config_vars = yaml.load(open(config_path))

# Initialize out celery app
celery_config = config_vars.get('celery', {'CELERY_BROKER_URL': ''})
celery = Celery("taxon", broker=config_vars['celery']['CELERY_BROKER_URL'])
celery.conf.update(celery_config)


def create_app(log_level=None, test=False, **kwargs):
    # initialize our flask application
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # inject all the yaml configs
    app.config.update(config_vars)
    app.config.update(kwargs)
    # set our template path
    template_path = app.config.get('TEMPLATE_PATH') or os.path.join(root, 'templates')
    app.jinja_loader = FileSystemLoader(template_path)
    # Remove the defaualt installed flask logger
    del app.logger.handlers[0]
    log_format = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s]: %(message)s')
    log_level = getattr(logging, log_level or app.config['log_level'])

    app.logger.setLevel(log_level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(log_format)
    app.logger.addHandler(handler)

    lm.init_app(app)
    lm.login_view = "/oauth/reddit"
    lm.login_message = None  # TODO: Remove after we add login page back in
    db.init_app(app)
    redis_store.init_app(app)
    oauth.init_app(app)

    # Monkey patch the celery task
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    hdlr = logging.FileHandler(app.config.get('log_file', 'webserver.log'))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    app.logger.addHandler(hdlr)
    app.logger.setLevel(logging.INFO)

    # Dynamically add all the filters in the filters.py file
    for name, func in inspect.getmembers(filters, inspect.isfunction):
        app.jinja_env.filters[name] = func

    # Error Handling
    # =========================================================================
    @app.errorhandler(Exception)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_web_error(error):
        # This fails sometimes, but I'm not sure why
        try:
            id = request.remote_addr if current_user.is_anonymous() else current_user.username
        except Exception:
            app.logger.exception("Exception handling error")
            id = None
        log_msg = "[{}] got error '{}' via url: '{}'".format(id, error, request.url)
        if app.config['DEBUG']:  # Only capture post data in debug mode
            log_msg += " with POST data : {}".format(list(request.values.items()))

        # Make sure we don't accidentally pass exception messages
        if (not hasattr(error, 'code')) or error.code not in [404, 403, 401]:
            app.logger.exception(log_msg)
            error = "500: Internal Server Error"
        else:
            app.logger.warning(log_msg)
        return render_template("error.html", no_header=True, error=error)

    @app.route("/exc_test")
    @app.route("/exc_test/<int:error>")
    def exception(error=None):
        app.logger.info("Exception test! Error: '{}'".format(error))
        exc = Exception() if error is None else abort(error)
        raise exc
        return ""

    # Route registration
    # =========================================================================
    from . import views, api
    app.register_blueprint(views.main)
    app.register_blueprint(api.api_blueprint, url_prefix='/api/v1')

    app.wsgi_app = ProxyFix(app.wsgi_app)
    return app
