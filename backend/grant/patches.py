from werkzeug import http, wrappers
import flask
from .werkzeug_http_fork import dump_cookie


def patch_werkzeug_set_samesite():
    http.dump_cookie = dump_cookie
    wrappers.base_response.dump_cookie = dump_cookie
