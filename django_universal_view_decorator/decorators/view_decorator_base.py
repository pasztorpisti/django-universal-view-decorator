import inspect
import types

from ..five import getfullargspec, full_qualname, raise_from
from ..utils import class_property, update_wrapper, wraps
from .view_class_decorator import view_class_decorator


class ViewDecoratorBase(object):
    """ Base class for view decorators that can be applied to both regular view functions and view class methods. It
    can also be converted into a "universal decorator" that makes it compatible also with view classes and makes it
    possible to omit the parameter list and the surrounding parents when optional decorator arguments are omitted. """

    # We define this empty logicless __init__ because otherwise under python2 the
    # `inspect.getargspec(cls.__init__)` statement fails in our `num_required_args`
    # classproperty implementation.
    def __init__(self):
        """ Override this and add some arguments to your `__init__()` implementation if you want your decorator
        to have arguments. Don't forget to upcall this super implementation in your `__init__()` """
        super(ViewDecoratorBase, self).__init__()

    def __call__(self, wrapped):
        """ Decorates/wraps a view function or view class method. """
        decoration_instance = _ViewDecoration(wrapped, self, self._call_view_function)
        self._on_decoration_instance_created(decoration_instance)
        return decoration_instance

    def _on_decoration_instance_created(self, decoration_instance):
        """ This decorator object isn't the wrapper around decorated objects. This is just a decorator that decorates
        them and most importantly: this is shared between them so don't store view-instance specific info in this
        object! In case of each decoration a separate wrapper object is created that is the decoration_instance.
        Override this method if you want to attach extra attributes to the wrapper when a view function or view class
        method is decorated. You can use those per-decoration attributes in the `_call_view_function()` that also
        receives the `decoration_instance` parameter. """
        pass

    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        """
        Override this to handle regular view functions, view classes, and view class methods in a unified way.
        :param view_class_instance: This is set only in case of decorated view class methods. In case of regular
        view functions and decorated classes it is `None`.
        """
        return view_function(*args, **kwargs)

    @class_property
    def num_required_args(cls):
        """
        Return None if no args are accepted by the decorator.
        Return -1 if there are only optional args and in case of zero args the `()` after the decorator is optional.
        Return the number of mandatory args otherwise. This can be 0, in that case the empty `()` has to be written
        after the decorator even if you pass zero args.
        By default this property never returns zero even if the number of non-default decorator args is zero. In such
        case this property returns -1 indicating that the `()` after the decorator is optional. If you want to make
        the `()` required in case of zero args you can explicitly set the `num_required_args = 0` class attribute on
        your decorator class.
        """
        argspec = getfullargspec(cls.__init__)
        if (len(argspec.args), argspec.varargs, argspec.varkw, argspec.defaults) == (1, None, None, None):
            return None
        result = len(argspec.args) - 1
        if argspec.defaults:
            result -= len(argspec.defaults)
        return result if result > 0 else -1

    @class_property
    def universal_decorator(cls):
        """ Returns a decorator that can be used to decorate regular view functions, view classes and view class
        methods. At the same time it handles optional decorator arguments. """
        num_required_args = cls.num_required_args
        if num_required_args is None:
            return cls.__transform_to_universal_decorator()

        def decorator_with_optional_args(*args, **kwargs):
            if num_required_args >= 0 or cls._are_decorator_args(args, kwargs):
                return cls.__transform_to_universal_decorator(*args, **kwargs)
            else:
                return cls.__transform_to_universal_decorator()(args[0])
        # for debugging
        decorator_with_optional_args.__name__ = '{}.universal_decorator_with_optional_args'.format(cls.__name__)
        return decorator_with_optional_args

    @classmethod
    def __transform_to_universal_decorator(cls, *args, **kwargs):
        """ Returns a decorator that auto-detects the type of the decorated object (regular view function, view
        class method, or view class) and applies this decorator class to it appropriately along with the extra
        decorator args. """
        # We instantiate the view_decorator outside of the _universal_decorator() closure in order to
        # avoid postponing problems with the decorator *args and **kwargs. This makes debugging easier.
        try:
            view_decorator = cls(*args, **kwargs)
        except TypeError as ex:
            raise_from(
                TypeError(
                    'This error may be the result of passing the wrong number of arguments to a view decorator.\n'
                    '  - decorator={decorator_name}\n  - args={args}\n  - kwargs={kwargs}'
                    .format(decorator_name=full_qualname(cls), args=args, kwargs=kwargs)
                ),
                ex,
            )

        def _universal_decorator(class_or_routine):
            if inspect.isroutine(class_or_routine):
                return view_decorator(class_or_routine)
            elif inspect.isclass(class_or_routine):
                return view_class_decorator(view_decorator)(class_or_routine)
            else:
                raise TypeError("Expected a regular view function, view class, or view class method, got {!r} instead."
                                .format(class_or_routine))
        # for debugging
        _universal_decorator.__name__ = '{}.universal_decorator'.format(cls.__name__)
        return _universal_decorator

    @classmethod
    def _are_decorator_args(cls, args, kwargs):
        """ This method decides whether the specified args and kwargs are the optional parameters for the
        decorator itself. If we have only a single positional argument without any kwargs then it may be difficult
        to decide whether the single argument is an arg for the decorator itself or a decoratable object.
        """
        if kwargs:
            return True
        if len(args) != 1:
            return True
        if not inspect.isroutine(args[0]) and not inspect.isclass(args[0]):
            return True
        return cls._is_decorator_arg(args[0])

    @classmethod
    def _is_decorator_arg(cls, arg):
        """ When the view decorator has no required args but it has at least 1 default arg (`num_required_args == 1`)
        then it is optional to provide the empty brackets `()` when you want to instantiate your decorator.
        There is only one problematic scenario: when the decorator receives only one argument it is difficult or
        impossible to find out whether this argument is an arg for the newly instantiated decorator, or a decoratable
        object that you want to decorate with the decorator that was instantiated without parameters without the
        optional empty brackets `()`:

        .. code-block:: python

            @my_decorator(only_one_default_positional_arg)
            def my_view(request):
                ...

            @my_decorator
            def my_view(request):
                ...


        In both cases the decorator receives only one argument. If the argument isn't a function, class, or class
        method then it is obviously a positional decorator argument so our decorator implementation can automatically
        detect this case. However if we face a pathological case where your decorator argument is a function, class, or
        class method then a human (you) has to deal with the problem. A very easy workaround is passing the decorator
        argument as a kwarg:

        .. code-block:: python

            @my_decorator(optional_first_positional_arg=only_one_default_positional_arg)
            def my_view(request):
                ....


        This way the decorator implementation will immediately know that this arg is a decorator arg and not a view that
        is being decorated. A more complicated way to deal with the problem is overriding the
        `ViewDecoratorBase._is_decorator_arg()` method and providing your own logic there to deal with this pathological
        case. This method is called only when the decorator has no required args, has at least 1 default arg and someone
        calls the decorator with only one argument that is a function, class, or class method. In this case your logic
        can help the decorator to decide. """
        return False


class _ViewDecoration(object):
    """ A decorator/wrapper for view functions and view class methods. An instance of this class is used as a
    wrapper object every time you decorate something with `ViewDecoratorBase`. The `decoration_instance` arg of
    the `ViewDecoratorBase._on_decoration_instance_created()` and `ViewDecoratorBase._call_view_function()` methods
    is an instance of this class. """
    def __init__(self, wrapped, view_decorator, call_view_function):
        assert inspect.isroutine(wrapped)

        # Calling update_wrapper() before assigning any instance attributes because
        # otherwise update_wrapper() might overwrite our things in self.__dict__.
        # For example by wrapping a view twice with this _ViewDecoration the instance attributes of
        # the second wrapper (like self.wrapped) could be overwritten by a not so well placed
        # update_wrapper() call.
        update_wrapper(self, wrapped)

        self.wrapped = wrapped
        # self.view_decorator for debugging
        self.view_decorator = view_decorator
        self.call_view_function = call_view_function

    def __call__(self, *args, **kwargs):
        # This is called when a decorated regular view function is called
        return self.call_view_function(self, None, self.wrapped, *args, **kwargs)

    def __get__(self, instance, owner=None):
        # This is called when a decorated view method is bound before calling it.
        bound_view_method = self.wrapped.__get__(instance, owner)

        @wraps(bound_view_method)
        def wrapper(self_2, *args, **kwargs):
            return self.call_view_function(self, self_2, bound_view_method, *args, **kwargs)
        return types.MethodType(wrapper, instance or owner)
