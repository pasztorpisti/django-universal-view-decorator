===============================
django-universal-view-decorator
===============================


.. image:: https://img.shields.io/travis/pasztorpisti/django-universal-view-decorator.svg?style=flat
    :target: https://travis-ci.org/pasztorpisti/django-universal-view-decorator
    :alt: build

.. image:: https://img.shields.io/codacy/c1087ff8de9a43a0bd87caefc7c96a81/master.svg?style=flat
    :target: https://www.codacy.com/app/pasztorpisti/django-universal-view-decorator
    :alt: code quality

.. image:: https://landscape.io/github/pasztorpisti/django-universal-view-decorator/master/landscape.svg?style=flat
    :target: https://landscape.io/github/pasztorpisti/django-universal-view-decorator/master
    :alt: code health

.. image:: https://img.shields.io/coveralls/pasztorpisti/django-universal-view-decorator/master.svg?style=flat
    :target: https://coveralls.io/r/pasztorpisti/django-universal-view-decorator?branch=master
    :alt: coverage

.. image:: https://img.shields.io/pypi/v/django-universal-view-decorator.svg?style=flat
    :target: https://pypi.python.org/pypi/django-universal-view-decorator
    :alt: pypi

.. image:: https://img.shields.io/github/tag/pasztorpisti/django-universal-view-decorator.svg?style=flat
    :target: https://github.com/pasztorpisti/django-universal-view-decorator
    :alt: github

.. image:: https://img.shields.io/github/license/pasztorpisti/django-universal-view-decorator.svg?style=flat
    :target: https://github.com/pasztorpisti/django-universal-view-decorator/blob/master/LICENSE.txt
    :alt: license: MIT

.. contents::


------------
Introduction
------------


In django you can implement views in two different standard ways (regular view function, class based view) and the same
project can make use of both techniques in parallel. In case of class based views I've seen several ways of decorating
them and none of the techniques were really attractive to me (visually and/or functionally).

You are probably familiar at least with the easiest ways of writing a decorator: implementing it as a regular function
(or class) and applying it only to regular view functions. Implementing a decorator that can be applied to both regular
view functions and instance methods is more challenging especially if you want to access the arguments of the decorated
function/method.

If we want to be able to apply the same decorator also to view classes then things get messy very quickly depending on
the expected behavior in that case.


Goals
-----

With this library I introduce a new way to implement django view decorators. At the same time I provide a
solution to reuse legacy decorators in a more flexible way.

The goals of this library:

- Easy way to implement view decorators that can be applied to:

  - regular view functions
  - view class methods
  - view classes

  If you have simple legacy view decorators that can be applied only to regular view functions then this library
  also provides a wrapper that makes your legacy decorator usable in the previously listed scenarios.

- The decorator implementation should be able to access view args (like `request`) easily in a unified way regardless
  of the type of the view the decorator is applied to.
- The way of applying the decorator to different kinds of views should look the same in the code. The code should have
  "good graphics". :-)
- Additional expectations in case of applying the decorator to view classes:

  - In case of applying the decorator to a view class I want the decorator to treat the view class as a regular
    view function. What do I mean by this? When you attach a view class to a url you call its `View.as_view()`
    method that basically converts it into a view function to be used by django. When I apply my decorator to a
    view class I want the decorator to decorate the view function returned by the `as_view()` method of the view
    class.
  - I want the decorator to be inherited by view subclasses and I want it to be difficult for subclasses to execute
    logic before the logic of the base class decorator. Simply overriding the `dispatch()` or `get()` or a
    similar method of the view subclass shouldn't allow code execution before the logic of a base class decorator.

    A difficult-to-bypass view base class decorator logic like this can come in handy in view base classes where you
    want to employ critical checks (security/permission related stuff). This inherited decorator can be a very good
    safeguard when others build on your subclasses and inherit your base class decorators.

    Anyway, if you want to provide base class view decoration logic before which a subclass can easily execute its own
    code then instead of decorating the base class you should probably decorate one of its methods (`dispatch()`,
    `get()`, etc...). This way the subclass can easily execute logic before base class method decorator simply by
    overriding the method.


-----
Usage
-----


Installation
------------

.. code-block:: sh

    pip install django-universal-view-decorator

Alternatively you can download the zipped library from https://pypi.python.org/pypi/django-universal-view-decorator


Quick-starter
-------------

Implementing decorators using this library
..........................................

I want an easy way to implement `@my_view_decorator` that can be applied easily to different kind of views in the
following way:

.. code-block:: python

    @my_view_decorator
    def regular_view_function(request):
        pass


    @my_view_decorator
    class ViewClass(View):
        ...


    class ViewClass2(View):
        @my_view_decorator(optional_param)
        def get(self, request):
            ...


The following code block is a possible implementation-skeleton of `@my_view_decorator` using this library.
Despite the long list of my requirements the implementation of the decorator is fairly simple:


.. code-block:: python

    from django_universal_view_decorator import ViewDecoratorBase


    class MyViewDecorator(ViewDecoratorBase):
        # Note: You don't have to override `__init__()` if your decorator doesn't
        # have arguments and you don't have to setup instance attributes.
        def __init__(self, optional_arg=5):
            super().__init__()
            self.optional_arg = optional_arg

        def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
            # Note: You can of course use `self.optional_arg` in this method.
            # If you need the request arg of the view...
            request = args[0]
            # TODO: manipulate the request and other incoming args/kwargs if you want
            # TODO: return a response instead of calling the original view if you want
            response = view_function(*args, **kwargs)
            # TODO: manipulate the response or forge a new one before returning it
            return response


    # This step makes the decorator compatible with view classes and also makes
    # it possible to use the decorator without the `()` when the decorator has
    # no required arguments and you don't want to pass any of them.
    my_view_decorator = MyViewDecorator.universal_decorator


Giving superpowers to legacy decorators
.......................................

Besides providing an easy way to implement the above "universal" view decorator I provide a special legacy decorator
wrapper that gives your legacy view decorators (that can be applied only to regular view functions) some of the
superpowers of the previously implemented universal view decorator.
This legacy decorator wrapper has to be applied similarly to `django.utils.decorators.method_decorator()`:


.. code-block:: python

    # Demonstrating the usage of the @universal_view_decorator provided by this library.
    from django_universal_view_decorator import universal_view_decorator


    @universal_view_decorator(your_legacy_decorator)
    def regular_view_function(request):
        pass


    @universal_view_decorator(legacy_decorator_with_parameters('woof', 'woof'))
    class ViewClass(View):
        ...


    class ViewClass2(View):
        @universal_view_decorator(legacy_decorator_1)
        @universal_view_decorator(legacy_decorator_2)
        def get(self, request):
            ...

        # this is equivalent in behavior to the decoration of `get()`
        @universal_view_decorator(legacy_decorator_1, legacy_decorator_2)
        def head(self, request):
            ...


-------------------------------------------------
I have a lot of time to read boring documentation
-------------------------------------------------


Popular view decoration techniques
----------------------------------

Here comes a brief and probably non-exhaustive collection of popular django view decoration techniques.
This section can be useful for quick "visual" comparison of the solutions (including mine).


Regular view functions
......................

Decorating a regular view function if fairly straightforward:

1.  You either simply apply the decorator to the regular view function...

    .. code-block:: python

        @legacy_decorator
        def regular_view_function(request):
            ...

2.  or you apply the decorator only on a per-url basis in your url config when you attach the view function to a
    specific url.

    .. code-block:: python

        urlpatterns = [
            url(r'^my/url/$', legacy_decorator(views.regular_view_function)),
            ...
        ]


Class based views
.................

In case of class based views things are a bit more complicated. Decorating view classes and view class methods is
more difficult than decorating regular view functions for several reasons including these:

- I think view classes and the related object oriented features (inheritance, etc..) make it a bit more difficult
  to trace the execution path of the logic. At the same time they make it more difficult to find the right spots to
  "insert" extra logic at the right spots for example by applying decorators.
- Writing decorators that manipulate classes in fancy ways isn't the easiest task.

Despite the previously mentioned problems I think class based views are useful but it doesn't change the fact that
people have been struggling with applying decorators to them. Probably as a consequence of this and maybe because of
the early lack of standard solutions people have hacked around and started using quite a few different solutions.

Decorating class based views:

1.  On a per-url basis in the url config when the class based view gets converted to a regular view function
    (by calling its `as_view()` class method). I think this is the most reliable way to decorate class based
    views, this is why my view class decorator uses the same insertion point for its decorator logic.

    .. code-block:: python

        urlpatterns = [
            url(r'^my/url/$', legacy_decorator(views.ViewClass.as_view())),
            ...
        ]

2.  By overriding its `dispatch()` method or one of the http-request-method specific methods called by `dispatch()`
    and decorating the method (usually with the help of `django.utils.decorators.method_decorator()` or using
    hand-crafted decorators that make use of ugly function or descriptor magic).

    .. code-block:: python

        class ViewClass(View):
            @method_decorator(legacy_decorator)
            def dispatch(self, request, *args, **kwargs):
                # We overridden this method without adding logic just
                # to be able to decorate it. This is a bit ugly.
                return super().dispatch(request, *args, **kwargs)

            @method_decorator(legacy_decorator_2)
            def get(self, request):
                ...

3.  The previous method decoration technique sometimes overrides a method (e.g.: `dispatch()`) just for the sake of
    decorating it. The implementation of the method in those cases simply calls the `super()` version. This is quite an
    ugly non-pythonic way that has two beautified versions:

    1.  You can apply your decorator to the method by applying the `django.utils.decorators.method_decorator()` to
        the view class by specifying the name of the method to decorate with the `name` arg of `method_decorator()`.
        (django>=1.9)

        .. code-block:: python

            @method_decorator(legacy_decorator, name='dispatch')
            class ViewClass(View):
                ...

    2.  Putting the overridden decorated method into a mixin class that can be added to the base class list of a class
        based view and can optionally be parametrized through class attributes. This mixin technique can be used
        without/instead of a decorator because the decorator logic can be put directly into the overridden method of
        the mixin class.

        .. code-block:: python

            class DecoratorMixin(object):
                """ Reusable mixin for class based views. """
                @method_decorator(legacy_decorator)
                def dispatch(self, request, *args, **kwargs):
                    return super().dispatch(request, *args, **kwargs)


            class DecoratorMixin2(object):
                """ Reusable mixin for class based views. """
                def get(self, request, *args, **kwargs):
                    # In this case we haven't actually used a decorator,
                    # we put the decorator logic directly to this method.
                    # TODO: manipulate input args if you want
                    response = super().get(request, *args, **kwargs)
                    # TODO: manipulate the response if you want
                    return response


            # The order of base classes is important!
            class ViewClass(DecoratorMixin, DecoratorMixin2, View):
                ...


Advanced view decorator features
--------------------------------


[TODO] Optional decorator arguments
...................................


[TODO] View class decorator inheritance explained
.................................................


[TODO] Managing duplicate view class decorators in the view class hierarchy
...........................................................................
