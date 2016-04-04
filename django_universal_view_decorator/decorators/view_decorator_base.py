import inspect
import types

from ..utils import class_property, update_wrapper, wraps
from .view_class_decorator import view_class_decorator


class ViewDecoratorBase(object):
    """ Base class for view decorators that can be applied to both regular view functions and view class methods. It
    can also be converted into a "universal decorator" that makes it compatible also with view classes and makes it
    possible to omit the parameter list and the surrounding parents when optional decorator arguments are omitted. """

    # We define this empty logicless __init__ because otherwise under python2 the
    # `inspect.getargspec(cls.__init__)` statement fails below in our `num_required_args`
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
        argspec = inspect.getargspec(cls.__init__)
        if (len(argspec.args), argspec.varargs, argspec.keywords, argspec.defaults) == (1, None, None, None):
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
                assert len(args)+len(kwargs) >= num_required_args, 'Decorator "{}" has {} required arguments'.format(
                    cls.__name__, num_required_args)
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
        def _universal_decorator(class_or_routine):
            view_decorator = cls(*args, **kwargs)
            if inspect.isroutine(class_or_routine):
                return view_decorator(class_or_routine)
            return view_class_decorator(view_decorator)(class_or_routine)
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
        """ If the decorator receives only a single positional argument and it is a routine or a class, then the
        automatic detection (the `_are_decorator_args()` method) can't decide whether this arg is a parameter for the
        decorator or a decoratable object. In that case this method has to decide. The default implementation always
        returns `False` so a single argument of routine or class type will be treated as a decoratable object.
        If you face this edge case you can either implement this method with some fancy logic or as an alternative
        workaround you can pass the single decorator argument as a kwarg instead of a positional argument. In that
        case `_are_decorator_args()` automatically finds out that this kwarg is for the decorator. """
        return False


class _ViewDecoration(object):
    """ A decorator/wrapper for view functions and view class methods. An instance of this class is used as a
    wrapper object every time you decorate something with `ViewDecoratorBase`. The `decoration_instance` arg of
    the `ViewDecoratorBase._on_decoration_instance_created()` and `ViewDecoratorBase._call_view_function()` methods
    is an instance of this class. """
    def __init__(self, wrapped, view_decorator, call_view_function):
        assert inspect.isroutine(wrapped)
        self.wrapped = wrapped
        update_wrapper(self, wrapped, updated=())
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
