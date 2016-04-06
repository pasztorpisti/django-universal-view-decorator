from .view_decorator_base import ViewDecoratorBase


class ViewRoutineDecorator(ViewDecoratorBase):
    # Currently we are using ViewRoutineDecorator directly without transforming it into a universal_decorator
    # but in case someone transformed it to a universal one it is better to make decorator arguments mandatory.
    # By default num_required_args is -1 for ViewRoutineDecorator because `__init__()` has only a `*decorators`
    # argument.
    num_required_args = 0

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
