import re

import mock
from django.test import TestCase

from django_universal_view_decorator import ViewDecoratorBase


def test_log(*args, **kwargs):
    pass


class TestAutomaticValueOfNumRequiredArgs(TestCase):
    """ If you don't override the `ViewDecoratorBase.num_required_args` class attribute then its value is
    dependent on the number of args of the `__init__()` of the concrete instantiated subclass of
    `ViewDecoratorBase`.

    Rules:
      - If `__init__()` has only a `self` argument then `num_required_args` is None. This means that the decorator
        receives no arguments and you can't use `()` after the decorator when you are applying it to a view.
      - If `__init__()` has at least one positional argument without a default value then `num_required_args` returns
        the number of positional args without a default value. This means that in case of applying the decorator
        you always have to specify at least the required arguments.
      - If `__init__()` has no positional arguments without a default value but it has at least one of the following:
            - positional arguments with default values
            - *args
            - **kwargs
        ... then `num_required_args` is -1 that means, you can apply the decorator to a view by specifying any of the
        optional arguments but if you don't specify any default args you can decide whether you want to use the
        empty arg-list brackets `()` after the decorator name. (Both @my_decorator and @my_decorator() are valid.)

        We don't test for python3 kwonlyargs but it doesn't matter because the presence of varargs is the important
        thing.
    """

    def test_init_has_only_self(self):
        # If `__init__()` has only a `self` arg then the decorator should not accept any args.
        # This means that `num_required_args` should be `None`.
        class MyDecorator(ViewDecoratorBase):
            def __init__(self):
                super(MyDecorator, self).__init__()

        self.assertIsNone(MyDecorator.num_required_args)

    def test_init_has_only_self_because_i_havent_defined_init_in_the_subclass(self):
        class MyDecorator(ViewDecoratorBase):
            pass

        self.assertIsNone(MyDecorator.num_required_args)

    def test_1_required_arg(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, required):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, 1)

    def test_2_required_args(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, required_0, required_1):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, 2)

    def test_required_arg_and_default_arg(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, required, default=None):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, 1)

    def test_default_arg(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, default=None):
                super(MyDecorator, self).__init__()

        # -1 means that we have 0 required args and the usage of `()` after the decorator is optional
        # if someone instantiates the decorator by passing no arguments.
        # e.g:
        #
        # my_decorator = MyDecorator.universal_decorator
        #
        # @my_decorator     # valid
        # class ViewClass(View):
        #     ...
        #
        # @my_decorator()    # valid
        # class ViewClass(View):
        #     ...
        self.assertEqual(MyDecorator.num_required_args, -1)

    def test_varargs(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, *args):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, -1)

    def test_kwargs(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, **kwargs):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, -1)

    def test_varargs_and_kwargs(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, *args, **kwargs):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, -1)

    def test_default_arg_and_kwargs(self):
        class MyDecorator(ViewDecoratorBase):
            def __init__(self, default=None, **kwargs):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, -1)


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestNumRequiredArgsHasExpectedEffectOnDecoratorArgPassing(TestCase):

    class MyDecoratorBase(ViewDecoratorBase):
        def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
            test_log('decorator')
            return view_function(*args, **kwargs)

    def test_num_required_args_is_none(self, mock_test_log):
        class MyDecorator(self.MyDecoratorBase):
            pass

        self.assertIsNone(MyDecorator.num_required_args)

        def view_function(request):
            test_log('view_function', request)
            return 'response'

        # decorating without decorator arguments should work
        response = MyDecorator.universal_decorator(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])

        # Decorating the big nothing gives a useful error message...
        # This decorator expects exactly one thing: the view to decorate.
        regexes = [
            "takes exactly 1 argument (0 given)",                                       # python2
            "missing 1 required positional argument: 'class_or_routine'",               # python3
            "MyDecorator.universal_decorator() takes exactly 1 argument (0 given)",     # pypy3
        ]
        pattern = '|'.join(re.escape(regex) for regex in regexes)
        self.assertRaisesRegexp(TypeError, pattern, MyDecorator.universal_decorator)

        # Decorating something that isn't a function, class, or class method should fail.
        self.assertRaisesRegexp(TypeError,
                                r"Expected a regular view function, view class, or view class method, got "
                                "'this_isnt_a_valid_view_to_decorate' instead\.",
                                MyDecorator.universal_decorator, 'this_isnt_a_valid_view_to_decorate')

    def test_num_required_args_is_minus_1(self, mock_test_log):
        # The decorator has no required args and MyDecorator.num_required_args == -1 that means it's optional
        # to write out the empty brackets `()` when we pass no args to the decorator.
        class MyDecorator(self.MyDecoratorBase):
            def __init__(self, arg=None):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, -1)

        def view_function(request):
            test_log('view_function', request)
            return 'response'

        # Should work without empty brackets.
        response = MyDecorator.universal_decorator(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])

        mock_test_log.reset_mock()

        # Empty brackets should work.
        response = MyDecorator.universal_decorator()(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])

        mock_test_log.reset_mock()

        # Passing the default decorator arg(s) should work.
        response = MyDecorator.universal_decorator('decorator_param')(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])

    def test_num_required_args_is_0(self, mock_test_log):
        class MyDecorator(self.MyDecoratorBase):
            # Note: the default implementation of the num_required_args attribute never returns 0. If you
            # have no required args then it returns -1 instead of 0 to allow omitting the empty brackets `()`
            # when you specify zero args for the decorator. You can however explicitly set this attribute to
            # zero when you know that your decorator has no required arguments. By doing so you force the users
            # of your decorator to write out the empty brackets even if they don't pass any decorator arguments
            # when applying it to a view.
            num_required_args = 0

        self.assertEqual(MyDecorator.num_required_args, 0)

        def view_function(request):
            test_log('view_function', request)
            return 'response'

        # Decorating a view without passing the required zero parameters (empty parents) to
        # the decorator shouldn't work.
        self.assertRaisesRegexp(
            TypeError,
            r'This error may be the result of passing the wrong number of arguments to a view decorator',
            MyDecorator.universal_decorator,
            view_function
        )

        response = MyDecorator.universal_decorator()(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])

    def test_num_required_args_is_1_or_more(self, mock_test_log):
        class MyDecorator(self.MyDecoratorBase):
            def __init__(self, arg):
                super(MyDecorator, self).__init__()

        self.assertEqual(MyDecorator.num_required_args, 1)

        def view_function(request):
            test_log('view_function', request)
            return 'response'

        # "Calling" the decorator with zero args should cause an error because the number of
        # required args is exactly 1.
        self.assertRaisesRegexp(
            TypeError,
            r'This error may be the result of passing the wrong number of arguments to a view decorator',
            MyDecorator.universal_decorator
        )

        response = MyDecorator.universal_decorator('decorator_param')(view_function)('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator'),
            mock.call('view_function', 'request'),
        ])


@mock.patch.object(ViewDecoratorBase, '_is_decorator_arg', return_value='is_decorator_arg_retval')
class TestAreDecoratorArgs(TestCase):
    """ Testing the `ViewDecoratorBase._are_decorator_args()` and `ViewDecoratorBase._is_decorator_arg()` methods."""

    def test_auto_detect_doesnt_work_on_single_positional_function_arg(self, mock_is_decorator_arg):
        def function_object(request):
            pass

        result = ViewDecoratorBase._are_decorator_args((function_object,), {})
        self.assertEqual(result, 'is_decorator_arg_retval')
        self.assertTrue(mock_is_decorator_arg.called)

    def test_auto_detect_doesnt_work_on_single_positional_class_arg(self, mock_is_decorator_arg):
        class MyClass(object):
            pass

        result = ViewDecoratorBase._are_decorator_args((MyClass,), {})
        self.assertEqual(result, 'is_decorator_arg_retval')
        self.assertTrue(mock_is_decorator_arg.called)

    def test_auto_detect_doesnt_work_on_single_positional_method_arg(self, mock_is_decorator_arg):
        class MyClass(object):
            def method(self):
                pass

        result = ViewDecoratorBase._are_decorator_args((MyClass.method,), {})
        self.assertEqual(result, 'is_decorator_arg_retval')
        self.assertTrue(mock_is_decorator_arg.called)

    def test_passing_kwargs_implies_decorator_args(self, mock_is_decorator_arg):
        def function_object(request):
            pass

        result = ViewDecoratorBase._are_decorator_args((), dict(arg=function_object))
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

        result = ViewDecoratorBase._are_decorator_args((function_object,), dict(kwarg='kwarg_value'))
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

    def test_args_count_other_than_1_implies_decorator_args(self, mock_is_decorator_arg):
        def function_object(request):
            pass

        result = ViewDecoratorBase._are_decorator_args((function_object, function_object), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

        result = ViewDecoratorBase._are_decorator_args((function_object, 'whatever'), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

    def test_non_routine_and_non_class_arg_implies_decorator_arg(self, mock_is_decorator_arg):
        result = ViewDecoratorBase._are_decorator_args(('non_routine_and_non_class',), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

        result = ViewDecoratorBase._are_decorator_args((None,), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

        result = ViewDecoratorBase._are_decorator_args((False,), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)

        result = ViewDecoratorBase._are_decorator_args((42,), {})
        self.assertTrue(result)
        self.assertFalse(mock_is_decorator_arg.called)
