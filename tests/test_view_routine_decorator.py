import functools
import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator import view_routine_decorator


def test_log(*args, **kwargs):
    pass


# Test decorators


class Decorator(object):
    def __init__(self, decorator_id):
        super(Decorator, self).__init__()
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


# Tests


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoration(TestCase):
    def test_regular_view_function(self, mock_test_log):
        @view_routine_decorator(decorator(1))
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('view_function', 'request'),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @view_routine_decorator(decorator(1))
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('dispatch', 'request'),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecorationUsingMultipleDecoratorParams(TestCase):
    def test_regular_view_function(self, mock_test_log):
        @view_routine_decorator(decorator(1), decorator(2))
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('view_function', 'request'),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @view_routine_decorator(decorator(1), decorator(2))
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('dispatch', 'request'),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestStackedDecoration(TestCase):
    def test_regular_view_function(self, mock_test_log):
        @view_routine_decorator(decorator(1))
        @view_routine_decorator(decorator(2), decorator(3))
        @view_routine_decorator(decorator(4))
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('view_function', 'request'),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @view_routine_decorator(decorator(1))
            @view_routine_decorator(decorator(2), decorator(3))
            @view_routine_decorator(decorator(4))
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('dispatch', 'request'),
        ])
