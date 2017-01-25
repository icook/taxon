import math
import rethinkdb

from . import redis_store, log, db


def vote(post_id, tag_id, user_id, up):
    ukey = post_id + "_" + tag_id + "_d"
    dkey = post_id + "_" + tag_id + "_u"

    redis_store.pfadd(ukey if up else dkey, user_id)
    uscore = redis_store.pfcount(ukey)
    dscore = redis_store.pfcount(dkey)
    score = uscore - dscore

    redis_store.zadd('top_' + tag_id, score, post_id)
    log.info("{user_id} voted up={up} for {tag_id} on {post_id}, new score {score}".format(**locals()))
    return score


def hot(score, date):
    order = math.log(max(abs(score), 1), 10)
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = date - 1134028003
    return str(round(sign * order + seconds / 45000, 7))


def unsubscribe(username, tag):
    rethinkdb.table("users").get(username).update(
        {'subscriptions': rethinkdb.row['subscriptions'].difference([tag])}
    ).run(db.conn)
    redis_store.zincrby('subscriptions', tag, amount=-1)


def subscribe(username, tag):
    rethinkdb.table("users").get(username).update(
        {'subscriptions': rethinkdb.row['subscriptions'].append(tag)}
    ).run(db.conn)
    redis_store.zincrby('subscriptions', tag)
