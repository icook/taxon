import rethinkdb

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

api_blueprint = Blueprint('api', __name__)

from . import lib, log, db


class APIException(Exception):
    def __init__(self, code, reason=None, desc=None):
        self.code = code
        self.reason = reason
        self.desc = desc


def abort(code, reason=None, desc=None):
    raise APIException(code, reason=reason, desc=desc)


@api_blueprint.errorhandler(APIException)
def handle_abort(error):
    return jsonify(success=False,
                   code=error.code,
                   reason=error.reason,
                   desc=error.desc), error.code


@api_blueprint.errorhandler(Exception)
def handle_api_error(error):
    log.error("Internal server error", exc_info=error)
    return jsonify(success=False,
                   code=500,
                   reason="internal_server_error",
                   desc=None), 500


@api_blueprint.route("/vote/<post_id>/<tag_id>/<direction>")
@login_required
def vote(post_id, tag_id, direction):
    up = direction == 'up'
    score = lib.vote(post_id, tag_id, current_user.username, up)
    return jsonify(success=True, new_score=score)


@api_blueprint.route("/posts/<comma_list>")
@login_required
def posts(comma_list):
    ids = comma_list.split(",")
    posts = rethinkdb.table("posts").get_all(*ids).run(db.conn)
    return jsonify(success=True, posts=list(posts))
