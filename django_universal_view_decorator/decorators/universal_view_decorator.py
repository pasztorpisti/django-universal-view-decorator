import inspect

from .view_routine_decorator import view_routine_decorator
from .view_class_decorator import view_class_decorator


class UniversalViewDecorator(object):
    """ Converts a decorator or a list of decorators into a universal decorator that can be applied to regular view
    functions, view class methods (for example to `View.dispatch()` or `View.get()`) and also to view classes.
    This is the combination of view_routine_decorator and view_class_decorator. """
    def __init__(self, *decorators):
        super(UniversalViewDecorator, self).__init__()
        self.decorators = decorators

    def __call__(self, wrapped):
        decorator = view_routine_decorator if inspect.isroutine(wrapped) else view_class_decorator
        return decorator(*self.decorators)(wrapped)


universal_view_decorator = UniversalViewDecorator
