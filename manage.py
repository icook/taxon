import os
import time
import sys
import logging
import requests
import pprint
import rethinkdb

from flask_script import Manager, Shell
from taxon import create_app, db

app = create_app()
manager = Manager(app)

root = os.path.abspath(os.path.dirname(__file__) + '/../')

from flask import current_app, _request_ctx_stack


@manager.option('-g', '--generate', default=False, action='store_true',
                help='makes a user account when regenerating')
def init_db(generate=False):
    """ Resets entire database to empty state """
    with app.app_context():
        connection = db.conn
        db_name = app.config['RETHINKDB_DB']
        r = rethinkdb

        try:
            r.db_drop(db_name).run(connection)
        except rethinkdb.RqlRuntimeError:
            pass
        r.db_create(db_name).run(connection)
        r.db(db_name).table_create('users', primary_key='username').run(connection)
        r.db(db_name).table_create('posts').run(connection)
        app.logger.info('Database setup completed')


@manager.command
def runserver():
    # When we run for dev from the command line it's nice to be able to use
    # print. By default Flask suppresses stdout and stderr
    if app.config['DEBUG']:
        class LoggerWriter:
            def __init__(self, logger, level):
                self.logger = logger
                self.level = level

            def write(self, message):
                if message != '\n':
                    self.logger.log(self.level, message)

            def flush(*args, **kwargs):
                pass

        sys.stdout = LoggerWriter(app.logger, logging.INFO)
        sys.stderr = LoggerWriter(app.logger, logging.INFO)

    current_app.run(host='127.0.0.1')


if __name__ == "__main__":
    manager.run()
