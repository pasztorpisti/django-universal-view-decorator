import json

from django.http import HttpResponse
from django.views.generic import View

from django_universal_view_decorator import universal_view_decorator

from .decorators import integerize_view_arg, increase_integer_view_arg


@integerize_view_arg
@universal_view_decorator(increase_integer_view_arg(increment=1))
def regular_view_function(request, number):
    return _create_json_response(dict(
        responder=regular_view_function.__name__,
        number=number,
    ))


@integerize_view_arg
@universal_view_decorator(increase_integer_view_arg(increment=-10))
class ViewClass(View):
    @universal_view_decorator(increase_integer_view_arg(increment=10))
    def get(self, request, number):
        return _create_json_response(dict(
            responder=type(self).__name__,
            number=number,
        ))


class ViewSubclass(ViewClass):
    pass


class ViewSubclass2(ViewClass):
    def get(self, request, number):
        # This get() override doesn't call the super implementation so the effect of the
        # increase_integer_view_arg(increment=10) has been eliminated in this subclass.
        return _create_json_response(dict(
            responder=type(self).__name__,
            number=number,
        ))


def _create_json_response(data):
    content = json.dumps(data)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Length'] = len(content)
    return response
