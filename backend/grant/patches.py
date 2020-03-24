import inspect
import textwrap

from werkzeug.wrappers.base_response import BaseResponse


def patch_werkzeug_set_samesite():
    BaseResponse_method_source = inspect.getsource(BaseResponse.set_cookie)

    BaseResponse_method_source = textwrap.dedent(BaseResponse_method_source)

    # Patch the code
    BaseResponse_method_source = BaseResponse_method_source.replace('samesite=None', 'samesite="None"')

    # This creates the function `patched_fn`
    patched_fn = exec(BaseResponse_method_source)

    # Replace the original function
    BaseResponse.set_cookie = patched_fn
