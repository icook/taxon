from . import redis_store, log


def vote(post_id, tag_id, user_id, up):
    ukey = post_id + "_" + tag_id + "_d"
    dkey = post_id + "_" + tag_id + "_u"

    redis_store.pfadd(ukey if up else dkey, user_id)
    uscore = redis_store.pfcount(ukey)
    dscore = redis_store.pfcount(dkey)
    score = uscore - dscore

    redis_store.zadd(tag_id, score, post_id)
    log.info("{user_id} voted up={up} for {tag_id} on {post_id}, new score {score}".format(**locals()))
    return score
