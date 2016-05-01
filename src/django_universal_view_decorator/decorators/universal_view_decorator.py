import inspect

from .view_class_decorator import view_class_decorator
from .view_routine_decorator import view_routine_decorator
from ..utils import wraps


def universal_view_decorator(*decorators, **duplicate_params):
    decorators = _wrap_decorators_if_needed(decorators, **duplicate_params)

    def decorate(view):
        if not decorators:
            return view
        decorator_wrapper = view_routine_decorator if inspect.isroutine(view) else view_class_decorator
        return decorator_wrapper(*decorators)(view)
    return decorate


def universal_view_decorator_with_args(decorator, **duplicate_params):
    def receive_decorator_args(*args, **kwargs):
        parametrized_decorator = decorator(*args, **kwargs)
        parametrized_decorator = _wrap_decorators_if_needed((parametrized_decorator,), **duplicate_params)[0]

        def decorate(view):
            decorator_wrapper = view_routine_decorator if inspect.isroutine(view) else view_class_decorator
            return decorator_wrapper(parametrized_decorator)(view)
        return decorate
    return receive_decorator_args


def _wrap_decorators_if_needed(decorators, duplicate_id=None, duplicate_handler_func=None,
                               duplicate_keep_newest=None, duplicate_priority=None):
    if duplicate_id is None and duplicate_handler_func is None and \
            duplicate_keep_newest is None and duplicate_priority is None:
        return decorators
    if duplicate_id is None:
        raise ValueError("You have used duplicate decorator related parameters without the 'duplicate_id' parameter")
    attributes = {}
    if duplicate_id is not None:
        attributes['decorator_duplicate_id'] = duplicate_id
    if duplicate_handler_func is not None:
        attributes['decorator_duplicate_handler_func'] = duplicate_handler_func
    if duplicate_keep_newest is not None:
        attributes['decorator_duplicate_keep_newest'] = duplicate_keep_newest
    if duplicate_priority is not None:
        attributes['decorator_duplicate_priority'] = duplicate_priority
    return tuple(_wrap_decorator_with_attributes(decorator, attributes) for decorator in decorators)


def _wrap_decorator_with_attributes(decorator, attributes):
    @wraps(decorator)
    def wrapper(*args, **kwargs):
        return decorator(*args, **kwargs)
    wrapper.__dict__.update(attributes)
    return wrapper
