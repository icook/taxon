import decimal

from flask import Blueprint, jsonify, request
from flask.ext.login import current_user

api_blueprint = Blueprint('api', __name__)

from . import lib, tasks, cfg, log


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


@api_blueprint.route("/me")
def me():
    if current_user.is_anonymous():
        abort(403, "access_denied", "You're not logged in")
    return jsonify(**current_user.json_prep())
