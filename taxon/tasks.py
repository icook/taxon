import praw
import praw.errors
import datetime
import praw.objects

from flask import render_template
from flask.ext.script import Manager
from itsdangerous import URLSafeSerializer

from . import celery, log, cfg


SchedulerCommand = Manager(usage='run celery tasks by hand')


@celery.task
@SchedulerCommand.command
def holder():
    pass
