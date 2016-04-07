import inspect

from .view_routine_decorator import view_routine_decorator
from .view_class_decorator import view_class_decorator


def universal_view_decorator(*decorators):
    def decorate(view):
        if not decorators:
            return view
        decorator_wrapper = view_routine_decorator if inspect.isroutine(view) else view_class_decorator
        return decorator_wrapper(*decorators)(view)
    return decorate


def universal_view_decorator_with_args(decorator):
    def receive_decorator_args(*args, **kwargs):
        parametrized_decorator = decorator(*args, **kwargs)

        def decorate(view):
            decorator_wrapper = view_routine_decorator if inspect.isroutine(view) else view_class_decorator
            return decorator_wrapper(parametrized_decorator)(view)
        return decorate
    return receive_decorator_args
