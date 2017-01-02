from . import redis_store, log


def vote(post_id, tag_id, user_id):
    key = post_id + "_" + tag_id
    redis_store.pfadd(key, user_id)
    score = redis_store.pfcount(key)
    redis_store.zadd(tag_id, score, post_id)
    log.info("{user_id} voted for {tag_id} on {post_id}, new score {score}".format(**locals()))
