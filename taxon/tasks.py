from flask_script import Manager

from . import celery


SchedulerCommand = Manager(usage='run celery tasks by hand')


@celery.task
@SchedulerCommand.command
def holder():
    pass
