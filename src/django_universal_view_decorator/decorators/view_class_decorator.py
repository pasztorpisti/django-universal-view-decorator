import collections
import inspect
import sys
import types

from ..utils import update_wrapper, wraps


class ViewClassDecorator(object):
    """ This is a view class decorator that hooks the `as_view()` method of the django view
    class and applies the specified decorator(s) to the return value of `as_view()`. """
    def __init__(self, *decorators):
        # receiving the parameters of our view class decorator
        super(ViewClassDecorator, self).__init__()
        self.decorators = decorators

    def __call__(self, class_to_decorate):
        # I've seen multiple inheritance in case of django views only with mixin usage, never by inheriting from
        # two or more `View` derivatives. For this reason and for the sake of simplicity this view class decorator
        # won't support that kind of multiple inheritance. This means that you can not put this decorator on view
        # mixins and if you inherit from two or more decorated `View` subclasses (but why would you do that???) then
        # your view class will inherit decorators only from the first one (that was listed first in the base class
        # list).

        # `accumulated_decorators` contains all view class decorators that have already been applied to this view class
        # along with the decorators it inherited from its view base class (if any). The decorators are in the correct
        # order in this tuple and the duplicates have already been eliminated from it. We are going to prepend our own
        # decorators to this list by eliminating any duplicate decorators if necessary.
        accumulated_decorators = getattr(class_to_decorate, '_accumulated_view_class_decorators', None)
        if accumulated_decorators is None:
            accumulated_decorators = ()
            # This view class or one of its view bases haven't yet been decorated. For this reason we decorate/hook
            # the as_view() classmethod of this view class.
            self.__decorate_the_as_view_method(class_to_decorate)

        setattr(class_to_decorate, '_accumulated_view_class_decorators',
                self._combine_our_decorators_with_accumulated_ones(class_to_decorate, accumulated_decorators))
        return class_to_decorate

    @staticmethod
    def __decorate_the_as_view_method(class_to_decorate):
        for base_class in inspect.getmro(class_to_decorate):
            as_view = base_class.__dict__.get('as_view')
            if as_view:
                class_to_decorate.as_view = _AsViewDecorator(as_view)
                break
        else:
            raise TypeError("The decorated view class ({}) doesn't have an as_view() method."
                            .format(class_to_decorate))

    def _combine_our_decorators_with_accumulated_ones(self, class_to_decorate, accumulated_decorators):
        """ Combines our decorators with the already accumulated ones. Accumulated decorators include decorators
        inherited from the base class along with decorators that have already been added to the currently decorated
        class using another `ViewClassDecorator` instance. """

        # creating a list of new and old/accumulated decorators
        decorators = [dict(decorator=decorator, view_class=class_to_decorate, group='new')
                      for decorator in self.decorators]
        for item in accumulated_decorators:
            item = item.copy()
            item['group'] = 'old'
            decorators.append(item)

        # collecting decorators that have the `decorator_duplicate_id` attribute
        duplicates = collections.defaultdict(list)
        for index, item in enumerate(decorators):
            duplicate_id = getattr(item['decorator'], 'decorator_duplicate_id', None)
            if duplicate_id is not None:
                item = item.copy()
                item['index'] = index
                duplicates[duplicate_id].append(item)

        # handling duplicate_ids one-by-one by calling a resolver function on them
        for duplicate_id, duplicates in duplicates.items():
            # skipping duplicate_id that has no new decorator or has less than 2 decorators in total
            if len(duplicates) < 2 or duplicates[0]['group'] != 'new':
                continue
            self._handle_duplicate_id(duplicate_id, duplicates, decorators)

        # Simplifying the items in the decorators array and dropping deleted/None items.
        return tuple(
            dict(decorator=item['decorator'], view_class=item['view_class'])
            for item in decorators if item is not None
        )

    def _handle_duplicate_id(self, duplicate_id, duplicates, decorators):
        # we create a copy because we will need it and the duplicates array
        # might be modified by the duplicate handler func
        duplicates_copy = [item.copy() for item in duplicates]

        duplicate_handler_func = self._get_decorator_attribute(duplicates, 'decorator_duplicate_handler_func',
                                                               self._default_duplicate_handler_func)
        duplicate_handler_func(duplicate_id, duplicates)
        assert len(duplicates) == len(duplicates_copy)

        # after the duplicate_handler_func() call each item in the duplicates array can be one of the following things:
        # 1. None: This means that the duplicate handler deleted this decorator.
        # 2. A dict that has a 'decorator' key: The duplicate handler either left this item unmodified or
        #    changed the value associated with the 'decorator' key.
        # 3. A decorator: The duplicate handler wants us to use this decorator instead of the old one.

        duplicates = [item['decorator'] if isinstance(item, dict) else item for item in duplicates]
        for i, decorator in enumerate(duplicates):
            decorators[duplicates_copy[i]['index']] = None if decorator is None else dict(
                decorator=decorator, view_class=duplicates_copy[i]['view_class'])

    def _default_duplicate_handler_func(self, duplicate_id, duplicates):
        """ This default duplicate handler func gets the priority of each duplicate and deletes all duplicates
        except one with the highest priority. If there are multiple decorators with the highest priority then we
        keep only the oldest from these - the one that was applied earlier to the same class one of the base classes.
        This order can be reversed by adding the `decorator_duplicate_keep_newest` attribute to the decorator with a
        True value - in this case if we have multiple decorators with the same highest priority we keep only the
        newest decorator that has been applied to last.

        The priority of the decorators is retrieved by getting the `decorator_duplicate_priority` attribute of the
        decorator object - if this attribute isn't present then the decorator automatically has a very low constant
        priority that is `-sys.maxsize`. If you specify a priority for your decorator using the
        `decorator_duplicate_priority` attribute then it should be an integral value.

        If you don't specify a priority for your decorators then all of them will have the default `-sys.maxint`
        priority so this default duplicate handler func always keeps only the oldest duplicate by default or
        the newest one if your decorator has the `decorator_duplicate_keep_newest = True` attribute. """
        keep_newest = self._get_decorator_attribute(duplicates, 'decorator_duplicate_keep_newest', False)
        index_to_keep = None
        kept_priority = -sys.maxsize - 1
        for index, item in (enumerate(duplicates) if keep_newest else reversed(list(enumerate(duplicates)))):
            priority = getattr(item['decorator'], 'decorator_duplicate_priority', -sys.maxsize)
            if priority > kept_priority:
                kept_priority = priority
                index_to_keep = index

        assert index_to_keep is not None
        for index in range(len(duplicates)):
            if index != index_to_keep:
                duplicates[index] = None

    _not_found = object()

    def _get_decorator_attribute(self, duplicates, attribute_name, default_value):
        for item in duplicates:
            value = getattr(item['decorator'], attribute_name, self._not_found)
            if value is not self._not_found:
                return value
        return default_value


view_class_decorator = ViewClassDecorator


class _AsViewDecorator(object):
    """ Used by `ViewClassDecorator` to decorate/hook the `as_view()` method of the decorated view class if necessary.
    This decorator applies decorator(s) to the view function returned by the decorated `as_view()`. """
    def __init__(self, wrapped_as_view):
        super(_AsViewDecorator, self).__init__()

        # Calling update_wrapper() before assigning any instance attributes
        # because otherwise update_wrapper() might overwrite our things in self.__dict__.
        update_wrapper(self, wrapped_as_view)

        self.wrapped_as_view = wrapped_as_view

    def __get__(self, instance, owner=None):
        bound_as_view = self.wrapped_as_view.__get__(instance, owner)

        @wraps(bound_as_view)
        def wrapper(cls, **initkwargs):
            view_function = bound_as_view(**initkwargs)
            for item in reversed(getattr(cls, '_accumulated_view_class_decorators')):
                view_function = item['decorator'](view_function)
            return view_function
        return types.MethodType(wrapper, owner or type(instance))
