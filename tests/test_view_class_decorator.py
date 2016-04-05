import functools
import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator import view_class_decorator
from django_universal_view_decorator.decorators.view_class_decorator import ViewClassDecorator


def test_log(*args, **kwargs):
    pass


# Test decorators


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


# Test view classes


@view_class_decorator(decorator('only_decorated_in_class_hierarchy'))
class OnlyDecoratedViewInClassHierarchy(View):
    def dispatch(self, request, *args, **kwargs):
        test_log('dispatch', OnlyDecoratedViewInClassHierarchy)
        return 'response'


@view_class_decorator(decorator('base'))
class BaseView(View):
    def dispatch(self, request, *args, **kwargs):
        test_log('dispatch', BaseView)
        return 'response'


@view_class_decorator(decorator('derived'), decorator('derived-b'))
class DerivedView(BaseView):
    def dispatch(self, request, *args, **kwargs):
        test_log('dispatch', DerivedView)
        return super(DerivedView, self).dispatch(request, *args, **kwargs)


@view_class_decorator(decorator('derived2'))
class DerivedView2(DerivedView):
    def dispatch(self, request, *args, **kwargs):
        test_log('dispatch', DerivedView2)
        return super(DerivedView2, self).dispatch(request, *args, **kwargs)


# Tests


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestDecoration(TestCase):
    def test_decorated_view_without_other_decorated_views_in_hierarchy(self, mock_test_log):
        response = OnlyDecoratedViewInClassHierarchy.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'only_decorated_in_class_hierarchy'),
            mock.call('dispatch', OnlyDecoratedViewInClassHierarchy),
        ])

    def test_decorated_view_with_decorated_subclass(self, mock_test_log):
        response = BaseView.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'base'),
            mock.call('dispatch', BaseView),
        ])

    def test_decorated_view_with_decorated_base_and_decorated_subclass(self, mock_test_log):
        response = DerivedView.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'derived'),
            mock.call('decorator', 'derived-b'),
            mock.call('decorator', 'base'),
            mock.call('dispatch', DerivedView),
            mock.call('dispatch', BaseView),
        ])

    def test_decorated_view_with_decorated_base_and_decorated_grand_base(self, mock_test_log):
        response = DerivedView2.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 'derived2'),
            mock.call('decorator', 'derived'),
            mock.call('decorator', 'derived-b'),
            mock.call('decorator', 'base'),
            mock.call('dispatch', DerivedView2),
            mock.call('dispatch', DerivedView),
            mock.call('dispatch', BaseView),
        ])


@mock.patch(__name__ + '.test_log', wraps=test_log)
class TestStackedDecoration(TestCase):
    def test_view_class_decorator_with_multiple_parameters(self, mock_test_log):
        @view_class_decorator(decorator(1), decorator(2))
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('dispatch'),
        ])

    def test_stacked_view_class_decorators(self, mock_test_log):
        @view_class_decorator(decorator(1))
        @view_class_decorator(decorator(2), decorator(3))
        @view_class_decorator(decorator(4))
        class ViewClass(View):
            def dispatch(self, request, *args, **kwargs):
                test_log('dispatch')
                return 'response'

        response = ViewClass.as_view()('request')
        self.assertEqual(response, 'response')
        self.assertListEqual(mock_test_log.mock_calls, [
            mock.call('decorator', 1),
            mock.call('decorator', 2),
            mock.call('decorator', 3),
            mock.call('decorator', 4),
            mock.call('dispatch'),
        ])


class TestInternals(TestCase):
    def test_as_view_method_gets_decorated_only_on_the_first_decorated_ancestor_view_class(self):
        with mock.patch.object(ViewClassDecorator, '_ViewClassDecorator__decorate_the_as_view_method',
                               wraps=getattr(ViewClassDecorator, '_ViewClassDecorator__decorate_the_as_view_method')) \
                               as mock_decorate_the_as_view_method:
            class BaseBase(View):
                pass

            @view_class_decorator(decorator(0))
            class Base(BaseBase):
                pass

            @view_class_decorator(decorator(1))
            class Derived1(Base):
                pass

            @view_class_decorator(decorator(2))
            class Derived2(Base):
                pass

            @view_class_decorator(decorator(21))
            class Derived2_1(Derived2):
                pass

            mock_decorate_the_as_view_method.assert_called_once_with(Base)


class TestDecorationErrors(TestCase):
    def test_trying_to_decorate_a_non_view_class_fails(self):
        class NonViewClass(object):
            pass

        self.assertRaisesMessage(
            TypeError,
            "The decorated view class ({}) doesn't have an as_view() method.".format(NonViewClass),
            view_class_decorator(decorator(0)),
            NonViewClass
        )
