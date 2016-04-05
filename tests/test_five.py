from django.test import TestCase

from django_universal_view_decorator.five import getfullargspec, FullArgSpec, qualname, raise_from, full_qualname


class TestGetFullArgSpec(TestCase):
    def test_no_args(self):
        def my_function():
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec([], None, None, None, [], None, {}))

    def test_1_arg(self):
        def my_function(arg):
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec(['arg'], None, None, None, [], None, {}))

    def test_1_default(self):
        def my_function(default=None):
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec(['default'], None, None, (None,), [], None, {}))

    def test_1_arg_1_default(self):
        def my_function(arg, default=None):
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec(
            ['arg', 'default'], None, None, (None,), [], None, {}))

    def test_1_arg_1_default_varargs(self):
        def my_function(arg, default=None, *args):
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec(
            ['arg', 'default'], 'args', None, (None,), [], None, {}))

    def test_1_arg_1_default_varargs_kwargs(self):
        def my_function(arg, default=None, *args, **kwargs):
            pass
        self.assertEqual(getfullargspec(my_function), FullArgSpec(
            ['arg', 'default'], 'args', 'kwargs', (None,), [], None, {}))


class QualNameTestClass(object):
    pass


def qualname_test_function():
    pass


class TestQualName(TestCase):
    def test_with_class(self):
        self.assertEqual(qualname(QualNameTestClass), 'QualNameTestClass')
        self.assertEqual(full_qualname(QualNameTestClass), 'tests.test_five.QualNameTestClass')

    def test_with_function(self):
        self.assertEqual(qualname(qualname_test_function), 'qualname_test_function')
        self.assertEqual(full_qualname(qualname_test_function), 'tests.test_five.qualname_test_function')


class TestRaiseFrom(TestCase):
    def test_raise_from_in_exception_handler(self):
        cause = Exception('cause')
        try:
            try:
                raise cause
            except Exception as ex1:
                raise_from(Exception('raised_from_cause'), ex1)
        except Exception as ex2:
            self.assertIs(getattr(ex2, '__cause__', None), cause)

    def test_raise_from_cause_that_isnt_the_exception_in_sys_exc_info(self):
        cause = Exception('cause')
        try:
            raise_from(Exception('raised_from_cause'), cause)
        except Exception as ex:
            self.assertIs(getattr(ex, '__cause__', None), cause)

    def test_raise_from_with_args_and_no_message(self):
        cause = Exception('cause')
        try:
            raise_from(Exception(0, 1), cause)
        except Exception as ex:
            self.assertIs(getattr(ex, '__cause__', None), cause)

    def test_raise_from_with_no_args_and_no_message(self):
        cause = Exception('cause')
        try:
            raise_from(Exception(), cause)
        except Exception as ex:
            self.assertIs(getattr(ex, '__cause__', None), cause)

    def test_both_message_and_args_set_but_they_are_different(self):
        cause = Exception('cause')
        try:
            ex = Exception(1, 2)
            ex.message = 'raised_from_cause'
            raise_from(ex, cause)
        except Exception as ex2:
            self.assertIs(getattr(ex2, '__cause__', None), cause)
