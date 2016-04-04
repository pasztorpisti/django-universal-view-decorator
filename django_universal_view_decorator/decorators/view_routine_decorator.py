from .view_decorator_base import ViewDecoratorBase


class ViewRoutineDecorator(ViewDecoratorBase):
    """ Converts a decorator or a list of decorators into a routine decorator that can be applied to both regular view
    functions and view class methods (for example to `View.dispatch()` or `View.get()`). """
    def __init__(self, *decorators):
        super(ViewRoutineDecorator, self).__init__()
        self.decorators = decorators

    def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
        for decorator in reversed(self.decorators):
            view_function = decorator(view_function)
        return view_function(*args, **kwargs)


view_routine_decorator = ViewRoutineDecorator
