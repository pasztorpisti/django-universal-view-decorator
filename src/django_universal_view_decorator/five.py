import sys
import inspect


__all__ = ['PY2', 'PY3', 'qualname', 'full_qualname', 'getfullargspec', 'FullArgSpec', 'raise_from',
           'update_wrapper', 'wraps']


PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3


def _simple_qualname(obj):
    if not hasattr(obj, '__name__') and hasattr(type(obj), '__name__'):
        obj = type(obj)
    return getattr(obj, '__name__', None) or repr(obj)


def full_qualname(obj):
    if not hasattr(obj, '__name__') and hasattr(type(obj), '__name__'):
        obj = type(obj)
    return getattr(obj, '__module__', '?') + '.' + qualname(obj)


if PY3:
    from inspect import getfullargspec, FullArgSpec
    from functools import update_wrapper, wraps


    def qualname(obj):
        if not hasattr(obj, '__name__') and hasattr(type(obj), '__name__'):
            obj = type(obj)
        return getattr(obj, '__qualname__', None) or _simple_qualname(obj)


    exec("""def raise_from(ex, cause):
    raise ex from cause
    """)


elif PY2:
    from collections import namedtuple
    from functools import partial, WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES
    import traceback

    # Under python2 we simulate the interface of the python3 getfullargspec(). Under python3 we have to use
    # getfullargspec() because getargspec() fails with ValueError in case of functions that have kwonlyargs.
    FullArgSpec = namedtuple('FullArgSpec', 'args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations')

    def getfullargspec(func):
        argspec = inspect.getargspec(func)
        # The first four items in FullArgSpec have the same meaning as the four
        # items of the older ArgSpec, they just have a different name in the tuple.
        full_argspec_items = argspec + ([], None, {})
        return FullArgSpec(*full_argspec_items)


    qualname = _simple_qualname


    def raise_from(ex, cause):
        ex.__cause__ = cause
        exc_info = sys.exc_info()
        if cause is exc_info[1]:
            cause_str = ''.join(traceback.format_exception(*exc_info))
        else:
            cause_str = repr(cause)

        if ex.message:
            if len(ex.args) != 1 or ex.args[0] != ex.message:
                ex.message = '{} args={!r}'.format(ex.message, ex.args)
        elif ex.args:
            ex.message = 'args={!r}'.format(ex.args)

        # Since the traceback of the last uncaught exception is printed by python before our exception message
        # I have to put the last exception of the chain to the top of the message. For this stupid reason our
        # chain will be printed in reverse order (compared to the usual stacktrace prints) but it is still more
        # usable than not having the chain.
        ex.message = '{orig_message}\n\n' \
                     '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n' \
                     'The following exception was the direct cause of the above exception:\n\n' \
                     '{cause_str}' \
                     .format(cause_str=cause_str, orig_message=ex.message)
        ex.args = ex.message,
        raise ex


    # Copy-pasted from the python3.5 functools implementation because the python2 implementation caused
    # AttributeError for me when the wrapped classonlymethod object had no __name__ attribute.
    def update_wrapper(wrapper,
                       wrapped,
                       assigned = WRAPPER_ASSIGNMENTS,
                       updated = WRAPPER_UPDATES):
        """Update a wrapper function to look like the wrapped function

           wrapper is the function to be updated
           wrapped is the original function
           assigned is a tuple naming the attributes assigned directly
           from the wrapped function to the wrapper function (defaults to
           functools.WRAPPER_ASSIGNMENTS)
           updated is a tuple naming the attributes of the wrapper that
           are updated with the corresponding attribute from the wrapped
           function (defaults to functools.WRAPPER_UPDATES)
        """
        for attr in assigned:
            try:
                value = getattr(wrapped, attr)
            except AttributeError:
                pass
            else:
                setattr(wrapper, attr, value)
        for attr in updated:
            getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
        # Issue #17482: set __wrapped__ last so we don't inadvertently copy it
        # from the wrapped function when updating __dict__
        wrapper.__wrapped__ = wrapped
        # Return the wrapper so this can be used as a decorator via partial()
        return wrapper


    # Copy-pasted from the python3.5 functools implementation because the python2 implementation caused
    # AttributeError for me when the wrapped classonlymethod object had no __name__ attribute.
    def wraps(wrapped,
              assigned = WRAPPER_ASSIGNMENTS,
              updated = WRAPPER_UPDATES):
        """Decorator factory to apply update_wrapper() to a wrapper function

           Returns a decorator that invokes update_wrapper() with the decorated
           function as the wrapper argument and the arguments to wraps() as the
           remaining arguments. Default arguments are as for update_wrapper().
           This is a convenience function to simplify applying partial() to
           update_wrapper().
        """
        return partial(update_wrapper, wrapped=wrapped,
                       assigned=assigned, updated=updated)
