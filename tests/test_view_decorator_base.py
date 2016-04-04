import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator import ViewDecoratorBase


def test_log(*args, **kwargs):
    pass


# Test views


def regular_view_function(request, *args, **kwargs):
    test_log(regular_view_function, request, *args, **kwargs)
    return 'response'


# Test decorators


class MyViewDecorator(ViewDecoratorBase):
    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        test_log(MyViewDecorator)
        return view_function(*args, **kwargs)


class MyViewDecoratorWithArg(ViewDecoratorBase):
    def __init__(self, *args, **kwargs):
        super(MyViewDecoratorWithArg, self).__init__()
        self.args = args
        self.kwargs = kwargs

    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        test_log(MyViewDecoratorWithArg, *self.args, **self.kwargs)
        args += self.args
        kwargs.update(self.kwargs)
        return view_function(*args, **kwargs)


class MyViewDecoratorThatDoesntCallTheView(ViewDecoratorBase):
    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        test_log(MyViewDecoratorThatDoesntCallTheView)
        return 'decorator_response'


# Tests


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoratingViewFunctionAndViewMethodWithoutUniversalWrapper(TestCase):
    def test_regular_view_function_without_decorator_args(self, mock_test_log):
        decorated = MyViewDecorator()(regular_view_function)
        response = decorated('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecorator),
            mock.call(regular_view_function, 'request'),
        ])

    def test_regular_view_function_with_decorator_args(self, mock_test_log):
        decorated = MyViewDecoratorWithArg(42)(regular_view_function)
        response = decorated('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, 42),
            mock.call(regular_view_function, 'request', 42),
        ])

    def test_view_class_method_without_decorator_args(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecorator()
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecorator),
            mock.call('dispatch', 'request'),
        ])

    def test_view_class_method_with_decorator_args(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorWithArg(42)
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, 42),
            mock.call('dispatch', 'request', 42),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoratingViewsWithUniversalWrapper(TestCase):
    def test_regular_view_function(self, mock_test_log):
        decorated = MyViewDecoratorWithArg.universal_decorator(42)(regular_view_function)
        response = decorated('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, 42),
            mock.call(regular_view_function, 'request', 42),
        ])

    def test_regular_view_function_with_decorator_that_doesnt_call_the_view(self, mock_test_log):
        decorated = MyViewDecoratorThatDoesntCallTheView.universal_decorator(regular_view_function)
        response = decorated('request')
        self.assertEqual(response, 'decorator_response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorThatDoesntCallTheView),
        ])

    def test_view_class_method(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorWithArg.universal_decorator(42)
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, 42),
            mock.call('dispatch', 'request', 42),
        ])

    def test_view_class_method_with_decorator_that_doesnt_call_the_view(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorThatDoesntCallTheView.universal_decorator
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'decorator_response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorThatDoesntCallTheView),
        ])

    def test_view_class(self, mock_test_log):
        @MyViewDecoratorWithArg.universal_decorator(42)
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, 42),
            mock.call('dispatch', 'request', 42),
        ])

    def test_view_class_with_decorator_that_doesnt_call_the_view(self, mock_test_log):
        @MyViewDecoratorThatDoesntCallTheView.universal_decorator
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'decorator_response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorThatDoesntCallTheView),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestStackedDecoration(TestCase):
    def test_regular_view_function_with_stacked_decorators(self, mock_test_log):
        @MyViewDecoratorWithArg(arg0=40)
        @MyViewDecoratorWithArg(arg1=41)
        @MyViewDecoratorWithArg(arg2=42)
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('view_function', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_view_class_method_with_stacked_decorators(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorWithArg(arg0=40)
            @MyViewDecoratorWithArg(arg1=41)
            @MyViewDecoratorWithArg(arg2=42)
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('dispatch', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_regular_view_function_with_stacked_universal_decorators(self, mock_test_log):
        @MyViewDecoratorWithArg.universal_decorator(arg0=40)
        @MyViewDecoratorWithArg.universal_decorator(arg1=41)
        @MyViewDecoratorWithArg.universal_decorator(arg2=42)
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('view_function', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_view_class_method_with_stacked_universal_decorators(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorWithArg.universal_decorator(arg0=40)
            @MyViewDecoratorWithArg.universal_decorator(arg1=41)
            @MyViewDecoratorWithArg.universal_decorator(arg2=42)
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('dispatch', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_view_class_with_stacked_universal_decorators(self, mock_test_log):
        @MyViewDecoratorWithArg.universal_decorator(arg0=40)
        @MyViewDecoratorWithArg.universal_decorator(arg1=41)
        @MyViewDecoratorWithArg.universal_decorator(arg2=42)
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('dispatch', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_regular_view_function_with_stacked_and_mixed_universal_and_non_universal_decorators(self, mock_test_log):
        @MyViewDecoratorWithArg(arg0=40)
        @MyViewDecoratorWithArg.universal_decorator(arg1=41)
        @MyViewDecoratorWithArg(arg2=42)
        def view_function(request, *args, **kwargs):
            test_log('view_function', request, *args, **kwargs)
            return 'response'

        response = view_function('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('view_function', 'request', arg0=40, arg1=41, arg2=42),
        ])

    def test_view_class_method_with_stacked_and_mixed_universal_and_non_universal_decorators(self, mock_test_log):
        class ViewClass(View):
            @MyViewDecoratorWithArg(arg0=40)
            @MyViewDecoratorWithArg.universal_decorator(arg1=41)
            @MyViewDecoratorWithArg(arg2=42)
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch', request, *args, **kwargs)
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call(MyViewDecoratorWithArg, arg0=40),
            mock.call(MyViewDecoratorWithArg, arg1=41),
            mock.call(MyViewDecoratorWithArg, arg2=42),
            mock.call('dispatch', 'request', arg0=40, arg1=41, arg2=42),
        ])
