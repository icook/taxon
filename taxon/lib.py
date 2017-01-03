from . import redis_store, log


def vote(post_id, tag_id, user_id, up):
    ukey = post_id + "_" + tag_id + "_d"
    dkey = post_id + "_" + tag_id + "_u"

    redis_store.pfadd(ukey if up else dkey, user_id)
    uscore = redis_store.pfcount(ukey)
    dscore = redis_store.pfcount(dkey)
    score = uscore - dscore

    #redis_store.lrange(tag_id, score, post_id)
    redis_store.zadd(tag_id, score, post_id)
    log.info("{user_id} voted up={up} for {tag_id} on {post_id}, new score {score}".format(**locals()))
    return score


class PostTag:
    def __init__(self, post, id, score=None):
        self.post = post
        self.id = id
        self._score = score

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Post:
    def __init__(self, json, scores):
        self.__dict__.update(**json)
        self.tags = [PostTag(self, t, scores.get(t)) for t in json['tags']]

    @property
    def composite_score(self):
        return sum([t._score or 0 for t in self.tags])

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
