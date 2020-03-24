import inspect
import textwrap

from werkzeug.wrappers import base_response
from .base_response_fork import BaseResponse


def patch_werkzeug_set_samesite():
    base_response.BaseResponse = BaseResponse