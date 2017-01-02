from . import redis_store, log


def vote(post_id, tag_id, user_id):
    key = post_id + "_" + tag_id
    redis_store.pfadd(key, user_id)
    score = redis_store.pfcount(key)
    redis_store.zadd(tag_id, score, post_id)
    log.info("{user_id} voted for {tag_id} on {post_id}, new score {score}".format(**locals()))


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
