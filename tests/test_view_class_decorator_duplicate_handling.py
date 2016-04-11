import functools
import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator.decorators.view_class_decorator import view_class_decorator


def test_log(*args, **kwargs):
    pass


# Test decorators


class Decorator(object):
    def __init__(self, duplicate_id, data=None, **extra_decorator_attributes):
        super(Decorator, self).__init__()
        self.duplicate_id = duplicate_id
        # We set self.decorator_duplicate_id to be used by view_class_decorator when doing duplicate check.
        self.decorator_duplicate_id = duplicate_id
        self.data = data
        self.__dict__.update(extra_decorator_attributes)

    def __call__(self, wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            test_log_kwargs = {} if self.data is None else {'data': self.data}
            test_log('decorator', self.duplicate_id, **test_log_kwargs)
            return wrapped(*args, **kwargs)
        return wrapper

    def __repr__(self):
        return '{}<0x{:08x}>({!r})'.format(type(self).__name__, hash(self) & 0xffffffff, self.duplicate_id)


decorator = Decorator


def _my_handle_duplicate_id(duplicate_id, duplicates, decorators):
    return [item.copy() for item in decorators]


@mock.patch.object(view_class_decorator, '_handle_duplicate_id', wraps=_my_handle_duplicate_id)
class TestHandleDuplicateIdCallsMadeAsExpected(TestCase):
    def setUp(self):
        self.decorator_0 = decorator(0)
        self.decorator_1 = decorator(1)
        self.decorator_2 = decorator(2)
        self.decorator_3 = decorator(3)

    def test_no_call_without_duplicate_decorator_in_current_view_class_decorator(self, mock_handle_duplicate_id):
        @view_class_decorator(self.decorator_0)
        class C0(View):
            pass

        # The class decorator hasn't introduced any duplicates.
        self.assertFalse(mock_handle_duplicate_id.called)

        # duplicates only in the newly added decorator list
        @view_class_decorator(self.decorator_1, self.decorator_2, self.decorator_1)
        class C1(C0):
            pass

        # The class decorator has introduced two new duplicate decorators with id=1.
        mock_handle_duplicate_id.assert_called_once_with(1, [
            dict(decorator=self.decorator_1, group='new', view_class=C1, index=0),
            dict(decorator=self.decorator_1, group='new', view_class=C1, index=2),
        ], [
            dict(decorator=self.decorator_1, group='new', view_class=C1),
            dict(decorator=self.decorator_2, group='new', view_class=C1),
            dict(decorator=self.decorator_1, group='new', view_class=C1),
            dict(decorator=self.decorator_0, group='old', view_class=C0),
        ])

        mock_handle_duplicate_id.reset_mock()

        @view_class_decorator(self.decorator_3)
        class C2(C1):
            pass

        # No handle_duplicate_id() call despite having old duplicates because the new decorators
        # applied to C2 (with id=3) have no duplicates even if we include the old/inherited decorators.
        self.assertFalse(mock_handle_duplicate_id.called)

        # The new decorator with id=0 is a duplicate of a previously added old decorator.
        @view_class_decorator(self.decorator_0)
        class C3(C2):
            pass

        mock_handle_duplicate_id.assert_called_once_with(0, [
            dict(decorator=self.decorator_0, group='new', view_class=C3, index=0),
            dict(decorator=self.decorator_0, group='old', view_class=C0, index=5),
        ], [
            dict(decorator=self.decorator_0, group='new', view_class=C3),
            dict(decorator=self.decorator_3, group='old', view_class=C2),
            dict(decorator=self.decorator_1, group='old', view_class=C1),
            dict(decorator=self.decorator_2, group='old', view_class=C1),
            dict(decorator=self.decorator_1, group='old', view_class=C1),
            dict(decorator=self.decorator_0, group='old', view_class=C0),
        ])

    def test_only_new_duplicates(self, mock_handle_duplicate_id):
        @view_class_decorator(self.decorator_0, self.decorator_1, self.decorator_0)
        class C0(View):
            pass

        mock_handle_duplicate_id.assert_called_once_with(0, [
            dict(decorator=self.decorator_0, group='new', view_class=C0, index=0),
            dict(decorator=self.decorator_0, group='new', view_class=C0, index=2),
        ], [
            dict(decorator=self.decorator_0, group='new', view_class=C0),
            dict(decorator=self.decorator_1, group='new', view_class=C0),
            dict(decorator=self.decorator_0, group='new', view_class=C0),
        ])

    def test_new_and_old_duplicate(self, mock_handle_duplicate_id):
        @view_class_decorator(self.decorator_0)
        class C0(View):
            pass

        self.assertFalse(mock_handle_duplicate_id.called)

        @view_class_decorator(self.decorator_1)
        class C1(C0):
            pass

        self.assertFalse(mock_handle_duplicate_id.called)

        # A simple case where a new decorator is a duplicate of a previous old one.
        @view_class_decorator(self.decorator_0)
        class C2(C1):
            pass

        mock_handle_duplicate_id.assert_called_once_with(0, [
            dict(decorator=self.decorator_0, group='new', view_class=C2, index=0),
            dict(decorator=self.decorator_0, group='old', view_class=C0, index=2),
        ], [
            dict(decorator=self.decorator_0, group='new', view_class=C2),
            dict(decorator=self.decorator_1, group='old', view_class=C1),
            dict(decorator=self.decorator_0, group='old', view_class=C0),
        ])

    def test_duplicate_between_two_view_class_decorators_applied_to_the_same_class(self, mock_handle_duplicate_id):
        # Two decorators with id=0 are applied to the same class with two separate @view_class_decorators.
        @view_class_decorator(self.decorator_0)
        @view_class_decorator(self.decorator_1)
        @view_class_decorator(self.decorator_0)
        @view_class_decorator(self.decorator_2)
        class C0(View):
            pass

        mock_handle_duplicate_id.assert_called_once_with(0, [
            dict(decorator=self.decorator_0, group='new', view_class=C0, index=0),
            dict(decorator=self.decorator_0, group='old', view_class=C0, index=2),
        ], [
            dict(decorator=self.decorator_0, group='new', view_class=C0),
            dict(decorator=self.decorator_1, group='old', view_class=C0),
            dict(decorator=self.decorator_0, group='old', view_class=C0),
            dict(decorator=self.decorator_2, group='old', view_class=C0),
        ])

    def test_duplicate_between_both_new_new_and_old_decorators_at_the_same_time(self, mock_handle_duplicate_id):
        @view_class_decorator(self.decorator_0)
        class C0(View):
            pass

        self.assertFalse(mock_handle_duplicate_id.called)

        # duplicate locally between two self.decorator_1 instances and also
        # between a new and old self.decorator_0
        @view_class_decorator(self.decorator_1, self.decorator_0, self.decorator_1)
        class C1(C0):
            pass

        self.assertEqual(mock_handle_duplicate_id.call_count, 2)
        mock_handle_duplicate_id.assert_has_calls([
            mock.call(0, [
                dict(decorator=self.decorator_0, group='new', view_class=C1, index=1),
                dict(decorator=self.decorator_0, group='old', view_class=C0, index=3),
            ], [
                dict(decorator=self.decorator_1, group='new', view_class=C1),
                dict(decorator=self.decorator_0, group='new', view_class=C1),
                dict(decorator=self.decorator_1, group='new', view_class=C1),
                dict(decorator=self.decorator_0, group='old', view_class=C0),
            ]),
            mock.call(1, [
                dict(decorator=self.decorator_1, group='new', view_class=C1, index=0),
                dict(decorator=self.decorator_1, group='new', view_class=C1, index=2),
            ], [
                dict(decorator=self.decorator_1, group='new', view_class=C1),
                dict(decorator=self.decorator_0, group='new', view_class=C1),
                dict(decorator=self.decorator_1, group='new', view_class=C1),
                dict(decorator=self.decorator_0, group='old', view_class=C0),
            ]),
        ], any_order=True)


@mock.patch.object(view_class_decorator, '_default_duplicate_handler_func', autospec=True,
                   side_effect=view_class_decorator._default_duplicate_handler_func)
@mock.patch.object(view_class_decorator, '_handle_duplicate_id', autospec=True,
                   side_effect=view_class_decorator._handle_duplicate_id)
@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDuplicateHandlerFuncCalledAsExpected(TestCase):
    """ Tests whether the right duplicate_handler_func is called. Every time a new @view_class_decorator is processed
    a duplicate decorator check is performed. If one of the new decorators (introduced by the new @view_class_decorator)
    is a duplicate of a new or old decorator (introduced by a previous @view_class_decorator) then the set of duplicate
    decorators is passed to the duplicate_handler func. The duplicate_handler_func can be provided by any of the
    duplicate decorators, they are checked in order (newest definition comes first) and the first duplicate handler
    function found will be used. If none of the duplicate decorators have a duplicate handler func then the default
    handler function of view_class_decorator is used that works with decorator priorities. If you decide not to use
    duplicate handler functions in your decorators then you can rely on the default duplicate handler func of
    view_class_decorator - in this case you can set priorities for your decorator instances with a specified attribute.
    """
    def setUp(self):
        self.decorator0_dup_id0 = decorator(0)
        self.decorator1_dup_id0 = decorator(0)
        self.decorator_dup_id1 = decorator(1)
        self.decorator_dup_id2 = decorator(2)

        def create_duplicate_handler(decorator_instance):
            def my_duplicate_handler(duplicate_id, duplicates):
                test_log(decorator_instance, duplicate_id, duplicates)
            return my_duplicate_handler

        self.decorator0_dup_id0.decorator_duplicate_handler_func = create_duplicate_handler(self.decorator0_dup_id0)
        self.decorator1_dup_id0.decorator_duplicate_handler_func = create_duplicate_handler(self.decorator1_dup_id0)
        self.decorator_dup_id1.decorator_duplicate_handler_func = create_duplicate_handler(self.decorator_dup_id1)
        self.decorator_dup_id2.decorator_duplicate_handler_func = create_duplicate_handler(self.decorator_dup_id2)

        self.decorator_nohandler_dup_id0 = decorator(0)

    def test_first_duplicate_handler_called_if_first_decorator_has_one(
            self, mock_test_log, mock_handle_duplicate_id, mock_default_duplicate_handler_func):
        # There are two decorators with id=0 so a duplicate handler will be called on them. The duplicate
        # decorators are checked in declaration order and the first one that has a duplicate handler function
        # will handle the duplicates. In this case self.decorator0_dup_id0 should handle it.
        class_decorator = view_class_decorator(
            self.decorator0_dup_id0,
            self.decorator_dup_id1,     # Not part of the duplicate checks because this is the only decorator with id=1
            self.decorator1_dup_id0,
            self.decorator_dup_id2,     # Not part of the duplicate checks because this is the only decorator with id=2
        )

        @class_decorator
        class C0(View):
            pass

        mock_test_log.assert_called_once_with(self.decorator0_dup_id0, 0, mock.ANY)
        mock_handle_duplicate_id.assert_called_once_with(class_decorator, 0, mock.ANY, mock.ANY)
        self.assertFalse(mock_default_duplicate_handler_func.called)

    def test_second_duplicate_handler_called_if_first_decorator_doesnt_have_a_duplicate_handler(
            self, mock_test_log, mock_handle_duplicate_id, mock_default_duplicate_handler_func):
        # There are two decorators with id=0 so a duplicate handler will be called on them. The duplicate
        # decorators are checked in declaration order and the first one that has a duplicate handler function
        # will handle the duplicates. In this case self.decorator1_dup_id0 should handle it.
        class_decorator = view_class_decorator(
            self.decorator_dup_id2,     # Not part of the duplicate checks because this is the only decorator with id=2
            self.decorator_nohandler_dup_id0,
            self.decorator_dup_id1,     # Not part of the duplicate checks because this is the only decorator with id=1
            self.decorator1_dup_id0,
        )

        @class_decorator
        class C0(View):
            pass

        mock_test_log.assert_called_once_with(self.decorator1_dup_id0, 0, mock.ANY)
        mock_handle_duplicate_id.assert_called_once_with(class_decorator, 0, mock.ANY, mock.ANY)
        self.assertFalse(mock_default_duplicate_handler_func.called)

    def test_default_duplicate_handler_called_if_duplicate_decorators_have_no_handler(
            self, mock_test_log, mock_handle_duplicate_id, mock_default_duplicate_handler_func):
        # There are two decorators with id=0 so a duplicate handler will be called on them. The duplicate
        # decorators are checked in declaration order and the first one that has a duplicate handler function
        # will handle the duplicates. Unfortunately in this case none of them has a duplicate handler function so
        # the default duplicate handler will be used (view_class_decorator._default_duplicate_handler_func).
        class_decorator = view_class_decorator(
            self.decorator_dup_id1,     # Not part of the duplicate checks because this is the only decorator with id=1
            self.decorator_nohandler_dup_id0,
            self.decorator_dup_id2,     # Not part of the duplicate checks because this is the only decorator with id=2
            self.decorator_nohandler_dup_id0,
        )

        @class_decorator
        class C0(View):
            pass

        self.assertFalse(mock_test_log.called)
        mock_handle_duplicate_id.assert_called_once_with(class_decorator, 0, mock.ANY, mock.ANY)
        mock_default_duplicate_handler_func.assert_called_once_with(class_decorator, 0, mock.ANY)


@mock.patch.object(view_class_decorator, '_default_duplicate_handler_func', autospec=True,
                   side_effect=view_class_decorator._default_duplicate_handler_func)
@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoratorListAndDecoratorViewExecutionAfterDuplicateHandlingIsAsExpected(TestCase):
    @staticmethod
    def _delete_all_but_the_newest_duplicate(duplicate_id, duplicates):
        for index in range(1, len(duplicates)):
            duplicates[index] = None

    @staticmethod
    def _delete_all_but_the_oldest_duplicate(duplicate_id, duplicates):
        for index in range(len(duplicates)-1):
            duplicates[index] = None

    @staticmethod
    def _replace_all_but_the_newest_duplicate(duplicate_id, duplicates):
        for index in range(1, len(duplicates)):
            duplicates[index] = decorator('replacement')

    def test_duplicate_decorator_delete_all_but_the_newest(self, mock_test_log, mock_default_duplicate_handler_func):
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0, decorator_duplicate_handler_func=self._delete_all_but_the_newest_duplicate),
            decorator(2),
            decorator(0),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertFalse(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 0),
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('dispatch'),
        ])

    def test_duplicate_decorator_delete_all_but_the_oldest(self, mock_test_log, mock_default_duplicate_handler_func):
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0, decorator_duplicate_handler_func=self._delete_all_but_the_oldest_duplicate),
            decorator(2),
            decorator(0),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertFalse(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 0),
            mock.call('dispatch'),
        ])

    def test_duplicate_decorator_replacement(self, mock_test_log, mock_default_duplicate_handler_func):
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0, decorator_duplicate_handler_func=self._replace_all_but_the_newest_duplicate),
            decorator(2),
            decorator(0),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertFalse(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 0),
            mock.call('decorator', 1),
            mock.call('decorator', 'replacement'),
            mock.call('decorator', 2),
            mock.call('decorator', 'replacement'),
            mock.call('dispatch'),
        ])

    def test_duplicate_decorator_deletion_and_replacement(self, mock_test_log, mock_default_duplicate_handler_func):
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0, decorator_duplicate_handler_func=self._replace_all_but_the_newest_duplicate),
            decorator(1, decorator_duplicate_handler_func=self._delete_all_but_the_newest_duplicate),
            decorator(2),
            decorator(1),
            decorator(0),
            decorator(1),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertFalse(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 0),
            mock.call('decorator', 1),
            mock.call('decorator', 'replacement'),
            mock.call('decorator', 2),
            mock.call('decorator', 'replacement'),
            mock.call('dispatch'),
        ])

    def test_duplicate_decorator_noop(self, mock_test_log, mock_default_duplicate_handler_func):
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0, decorator_duplicate_handler_func=lambda *args: None),
            decorator(2),
            decorator(0),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertFalse(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 0),
            mock.call('decorator', 1),
            mock.call('decorator', 0),
            mock.call('decorator', 2),
            mock.call('decorator', 0),
            mock.call('dispatch'),
        ])


@mock.patch.object(view_class_decorator, '_default_duplicate_handler_func', autospec=True,
                   side_effect=view_class_decorator._default_duplicate_handler_func)
@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDefaultDuplicateHandlerFuncLogic(TestCase):
    def test_same_priority_keeps_oldest_decorator_by_default(self, mock_test_log, mock_default_duplicate_handler_func):
        # We haven't specified a priority for the decorators so all of them have priority=-sys.maxint.
        # We have multiple decorators with id=0, since their priority is the same the duplicate handler
        # will keep only the oldest.
        @view_class_decorator(
            decorator(0),
            decorator(1),
            decorator(0),
            decorator(2),
            decorator(0, data='oldest'),
            decorator(3),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertTrue(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 0, data='oldest'),
            mock.call('decorator', 3),
            mock.call('dispatch'),
        ])

    def test_same_priority_keeps_newest_when_explicitly_asked_to_do_so(
            self, mock_test_log, mock_default_duplicate_handler_func):
        # We haven't specified a priority for the decorators so all of them have priority=-sys.maxint.
        # We have multiple decorators with id=0, since their priority is the same the duplicate handler
        # will keep only the newest because at least one of the duplicate decorators has a
        # `decorator_duplicate_keep_newest` attribute with a True value.
        @view_class_decorator(
            decorator(0, data='newest'),
            decorator(1),
            decorator(0, decorator_duplicate_keep_newest=True),
            decorator(2),
            decorator(0),
            decorator(3),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertTrue(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 0, data='newest'),
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('dispatch'),
        ])

    def test_same_priority_keeps_oldest_decorator_with_user_defined_priorities(
            self, mock_test_log, mock_default_duplicate_handler_func):
        # We haven't specified a priority for the decorators so all of them have priority=-sys.maxint.
        # We have multiple decorators with id=0, since their priority is the same the duplicate handler
        # will keep only the oldest.
        @view_class_decorator(
            decorator(1),
            decorator(0, decorator_duplicate_priority=42),
            decorator(0, decorator_duplicate_priority=42),
            decorator(0, decorator_duplicate_priority=42),
            decorator(2),
            decorator(0, decorator_duplicate_priority=42, data='oldest'),
            decorator(3),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertTrue(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 0, data='oldest'),
            mock.call('decorator', 3),
            mock.call('dispatch'),
        ])

    def test_same_priority_keeps_newest_decorator_with_user_defined_priorities(
            self, mock_test_log, mock_default_duplicate_handler_func):
        # We haven't specified a priority for the decorators so all of them have priority=-sys.maxint.
        # We have multiple decorators with id=0, since their priority is the same the duplicate handler
        # will keep only the newest because at least one of the duplicate decorators has a
        # `decorator_duplicate_keep_newest` attribute with a True value.
        @view_class_decorator(
            decorator(1),
            decorator(0, decorator_duplicate_priority=42, data='newest'),
            decorator(0, decorator_duplicate_priority=42),
            decorator(0, decorator_duplicate_priority=42, decorator_duplicate_keep_newest=True),
            decorator(2),
            decorator(0, decorator_duplicate_priority=42),
            decorator(3),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertTrue(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 0, data='newest'),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('dispatch'),
        ])

    def test_user_defined_priorities(self, mock_test_log, mock_default_duplicate_handler_func):
        # Duplicate decorators with id=0. The default duplicate handler func should keep the one
        # with the highest priority.
        @view_class_decorator(
            decorator(0),   # the default priority for this decorator is -sys.maxint
            decorator(1),
            decorator(0, decorator_duplicate_priority=2, data='winner'), # highest priority
            decorator(2),
            decorator(0, decorator_duplicate_priority=-1),
            decorator(3),
            decorator(0, decorator_duplicate_priority=0),
            decorator(0, decorator_duplicate_priority=1),
        )
        class C0(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = C0.as_view()('request')
        self.assertEqual(response, 'response')

        self.assertTrue(mock_default_duplicate_handler_func.called)
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 0, data='winner'),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('dispatch'),
        ])
