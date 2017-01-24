import rethinkdb
import itertools
import time

from flask_script import Manager

from . import celery, redis_store, log, db
from .lib import hot


SchedulerCommand = Manager(usage='run celery tasks by hand')


@celery.task
@SchedulerCommand.command
def update_hot():
    t = time.time()
    tags = redis_store.keys("top_*")
    for tag_key in tags:
        tag_key = tag_key.decode('utf8')
        # Load all the current scores
        batch = {r[0].decode('utf8'): r[1] for r in redis_store.zscan_iter(tag_key)}
        # Replace the regular score with the calculated hot score. Kinda sloppy
        # doing it in place...
        for post in rethinkdb.table("posts").get_all(*batch.keys()).run(db.conn):
            batch[post['id']] = hot(batch[post['id']], post['posted_at'])
        # We need to reverse keys and values unfortunately...
        reverse_generator = ((v, k) for k, v in batch.items())
        # Now pass that list to redis to update. This should be batched soon
        redis_store.zadd('hot_' + tag_key[4:], *itertools.chain.from_iterable(reverse_generator))
        log.info("Updating hot for {}".format(tag_key[4:]))
    log.info("Ran in {:,.5}ms".format((time.time() - t) * 1000))


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, update_hot, name='update hot')
