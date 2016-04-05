import sys
import inspect


__all__ = ['PY2', 'PY3', 'qualname', 'full_qualname', 'getfullargspec', 'FullArgSpec', 'raise_from']


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


    def qualname(obj):
        if not hasattr(obj, '__name__') and hasattr(type(obj), '__name__'):
            obj = type(obj)
        return getattr(obj, '__qualname__', None) or _simple_qualname(obj)


    exec("""def raise_from(ex, cause):
    raise ex from cause
    """)


elif PY2:
    from collections import namedtuple
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

else:
    raise RuntimeError('This stuff should be executed under python2.7+ or python3.3+')
