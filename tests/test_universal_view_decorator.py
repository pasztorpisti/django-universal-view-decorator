import functools
import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator import universal_view_decorator


def test_log(*args, **kwargs):
    pass


class Decorator(object):
    def __init__(self, decorator_id):
        self.decorator_id = decorator_id

    def __call__(self, wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            test_log('decorator', self.decorator_id)
            return wrapped(*args, **kwargs)
        return wrapper

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.decorator_id)


decorator = Decorator


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoration(TestCase):
    def test_regular_view_function(self, mock_test_log):
        @universal_view_decorator(decorator('regular'))
        def view_function(request, *args, **kwargs):
            test_log('view_function', view_function)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'regular'),
            mock.call('view_function', view_function),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @universal_view_decorator(decorator('view_method'))
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', ViewClass)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'view_method'),
            mock.call('dispatch', ViewClass),
        ])

    def test_view_class(self, mock_test_log):
        @universal_view_decorator(decorator('view_class'))
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', ViewClass)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'view_class'),
            mock.call('dispatch', ViewClass),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecorationWithStackedDecorators(TestCase):
    def test_regular_view_function(self, mock_test_log):
        @universal_view_decorator(decorator(1))
        @universal_view_decorator(decorator(2), decorator(3))
        @universal_view_decorator(decorator(4))
        def view_function(request, *args, **kwargs):
            test_log('view_function', view_function)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('view_function', view_function),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @universal_view_decorator(decorator(1))
            @universal_view_decorator(decorator(2), decorator(3))
            @universal_view_decorator(decorator(4))
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', ViewClass)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('dispatch', ViewClass),
        ])

    def test_view_class(self, mock_test_log):
        @universal_view_decorator(decorator(1))
        @universal_view_decorator(decorator(2), decorator(3))
        @universal_view_decorator(decorator(4))
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', ViewClass)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('dispatch', ViewClass),
        ])
