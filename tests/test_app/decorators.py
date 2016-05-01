import numbers
from functools import wraps
from django_universal_view_decorator import ViewDecoratorBase, universal_view_decorator_with_args


class _IntegerizeViewArg(ViewDecoratorBase):
    decorator_duplicate_id = 'IntegerizeViewArg'
    decorator_duplicate_keep_newest = True

    def __init__(self, view_arg_name='number'):
        super(_IntegerizeViewArg, self).__init__()
        self.view_arg_name = view_arg_name

    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        integer_str = kwargs.get(self.view_arg_name)
        assert not isinstance(integer_str, numbers.Integral)
        kwargs[self.view_arg_name] = int(integer_str)
        return view_function(*args, **kwargs)


integerize_view_arg = _IntegerizeViewArg.universal_decorator


def increase_integer_view_arg(view_arg_name='number', increment=10):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapper(*args, **kwargs):
            number = kwargs[view_arg_name]
            assert isinstance(number, int)
            kwargs[view_arg_name] = number + increment
            return wrapped(*args, **kwargs)
        return wrapper
    return decorator


wrapped_increase_integer_view_arg = universal_view_decorator_with_args(increase_integer_view_arg)
