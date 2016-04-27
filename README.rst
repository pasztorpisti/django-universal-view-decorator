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

I've seen several discussions on mailing lists about modifying view class behavior with decorators VS mixins. While
it's obviously easier to use decorators with regular functions I think they have some limited use also in case of
classes. I don't expect you to see this library as THE solution to all of your previous problems. Both decorators and
mixins have their own problems in case of view classes. It depends on the scenario which solution is less painful to
apply.


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
  also provides wrappers that make your legacy decorator usable in the previously mentioned scenarios.

- The decorator implementation should be able to access view args (like ``request``) easily in a unified way regardless
  of the type of the view the decorator is applied to.
- The way of applying the decorator to different kinds of views should look the same in the code. The code should have
  "good graphics". :-)
- Additional expectations in case of applying the decorator to view classes:

  - In case of applying the decorator to a view class I want the decorator to treat the view class as a regular
    view function. What do I mean by this? When you attach a view class to a url you call its ``View.as_view()``
    method that basically converts it into a view function to be used by django. When I apply my decorator to a
    view class I want the decorator to decorate the view function returned by the ``as_view()`` method of the view
    class.
  - I want the decorator to be inherited by view subclasses and I want it to be difficult for subclasses to execute
    logic before the logic of the base class decorator. Simply overriding the ``dispatch()`` or ``get()`` or a
    similar method of the view subclass shouldn't allow code execution before the logic of a base class decorator.

    A difficult-to-bypass view base class decorator logic like this can come in handy in view base classes where you
    want to employ critical checks (security/permission related stuff). This inherited decorator can be a very good
    safeguard when others implement their subclasses by building on your base class and inherit your base class
    decorators.

    Anyway, if you want to provide base class view decoration logic before which a subclass can easily execute its own
    code then instead of decorating the base class you should probably decorate one of its methods (``dispatch()``,
    ``get()``, etc...). This way the subclass can easily execute logic before base class method decorator simply by
    overriding the method.


-----
Usage
-----


Installation
------------

.. code-block:: sh

    pip install django-universal-view-decorator

Alternatively you can download the distribution from the following places:

- https://pypi.python.org/pypi/django-universal-view-decorator#downloads
- https://github.com/pasztorpisti/django-universal-view-decorator/releases


Quick-starter
-------------

Implementing decorators using this library
..........................................

I want an easy way to implement ``@my_view_decorator`` that can be applied easily to different kind of views in the
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


The following code block is a possible implementation-skeleton of ``@my_view_decorator`` using this library.
Despite the long list of my requirements the implementation of the decorator is fairly simple:


.. code-block:: python

    from django_universal_view_decorator import ViewDecoratorBase


    class MyViewDecorator(ViewDecoratorBase):
        # Note: You don't have to override ``__init__()`` if your decorator doesn't
        # have arguments and you don't have to setup instance attributes.
        def __init__(self, optional_arg=5):
            super().__init__()
            self.optional_arg = optional_arg

        def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
            # Note: You can of course use ``self.optional_arg`` in this method.
            # If you need the request arg of the view...
            request = args[0]
            # TODO: manipulate the request and other incoming args/kwargs if you want
            # TODO: return a response instead of calling the original view if you want
            response = view_function(*args, **kwargs)
            # TODO: manipulate the response or forge a new one before returning it
            return response


    # This step makes the decorator compatible with view classes and also makes
    # it possible to use the decorator without the ``()`` when the decorator has
    # no required arguments and you don't want to pass any of them.
    my_view_decorator = MyViewDecorator.universal_decorator


Giving superpowers to legacy decorators
.......................................

Besides providing an easy way to implement the above "universal" view decorator this library also provides special
legacy decorator wrappers that give your legacy view decorators (that can be applied only to regular view functions)
some of the superpowers of the previously implemented universal view decorator.
These legacy decorator wrappers have to be applied similarly to ``django.utils.decorators.method_decorator()``:


1.  Use the ``universal_view_decorator`` wrapper when:

    - your legacy decorator has no arguments
    - your legacy decorator has arguments but it's ok to pass the arguments to your legacy decorator BEFORE wrapping it


    .. code-block:: python

        from django_universal_view_decorator import universal_view_decorator


        @universal_view_decorator(legacy_decorator)
        def regular_view_function(request):
            ...


        # You can wrap multiple decorators at the same time
        @universal_view_decorator(legacy_decorator, legacy_decorator_2)
        def regular_view_function(request):
            ...


        # This double decoration is equivalent in behavior to the previous example
        # where we used one wrapper to wrap both legacy decorators.
        @universal_view_decorator(legacy_decorator)
        @universal_view_decorator(legacy_decorator_2)
        def regular_view_function(request):
            ...


        # With ``@universal_view_decorator`` you have to pass the args to your legacy
        # decorators BEFORE wrapping them. If you want to pass the args to your decorator
        # after wrapping then you have to use the ``@universal_view_decorator_with_args``
        # instead of this wrapper.
        @universal_view_decorator(legacy_decorator_with_args(arg))
        def regular_view_function(request):
            ...


        # Applying the decorator to view classes
        @universal_view_decorator(legacy_decorator_with_args('woof', 'woof'))
        class ViewClass(View):
            ...


        # Applying the decorator to view class methods
        class ViewClass(View):
            @universal_view_decorator(legacy_decorator, legacy_decorator_2)
            def head(self, request):
                ...


        # Reusable wrapped decorator
        reusable_wrapped_legacy_decorator = universal_view_decorator(legacy_decorator_with_args(5))


        @reusable_wrapped_legacy_decorator
        class ViewClass(View):
            ...



2.  Use the ``universal_view_decorator_with_args`` wrapper when your decorator has args and you want to pass these args
    to your legacy decorator AFTER wrapping it. With this wrapper you can't wrap multiple legacy decorators at the
    same time.

    .. code-block:: python

        from django_universal_view_decorator import universal_view_decorator_with_args


        # Wrapping the legacy decorator and the reusing the wrapped one multiple times.
        wrapped_legacy_decorator = universal_view_decorator_with_args(legacy_decorator_with_args)


        @wrapped_legacy_decorator(legacy_decorator_arg)
        def regular_view_function(request):
            ...


        @wrapped_legacy_decorator(arg1, arg2, kwarg1=1, kwarg2='woof')
        class ViewClass(View):
            ...


        class ViewClass(View):
            @wrapped_legacy_decorator(arg1, arg2, kwarg1=1, kwarg2='woof')
            def get(self, request):
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
  "insert" extra logic for example by applying decorators.
- Writing decorators that manipulate classes in fancy and perhaps useful ways isn't the easiest task.

Despite the previously mentioned problems I think class based views are useful but it doesn't change the fact that
people have been struggling with applying decorators (or other "behavior modifiers") to them. Probably as a consequence
of this and maybe because of the early lack of standard solutions people have hacked around and forged quite a few
different solutions.

Decorating class based views:

1.  On a per-url basis in the url config when the class based view gets converted to a regular view function
    (by calling its ``as_view()`` class method). I think this is the most reliable and easy-to-understand way to decorate
    class based views. This is why my view class decorator uses the same insertion point for its decorator logic.
    The decorator logic sits in a well defined place exactly between the django url dispatcher and the view function.

    .. code-block:: python

        urlpatterns = [
            url(r'^my/url/$', legacy_decorator(views.ViewClass.as_view())),
            ...
        ]

2.  By overriding its ``dispatch()`` method or one of the http-request-method specific methods called by ``dispatch()``
    and decorating the method (usually with the help of ``django.utils.decorators.method_decorator()`` or using
    hand-crafted decorators that make use of ugly function or descriptor magic).

    .. code-block:: python

        from django.utils.decorators import method_decorator

        class ViewClass(View):
            @method_decorator(legacy_decorator)
            def dispatch(self, request, *args, **kwargs):
                # We overridden this method without adding logic just
                # to be able to decorate it. This is a bit ugly.
                return super().dispatch(request, *args, **kwargs)

            @method_decorator(legacy_decorator_2)
            def get(self, request):
                ...

3.  The previous method decoration technique sometimes overrides a method (e.g.: ``dispatch()``) just for the sake of
    decorating it. The implementation of the method in that case simply calls the ``super()`` version. This is quite an
    ugly non-pythonic way that has two beautified versions:

    1.  You can apply your decorator to the method by applying the ``django.utils.decorators.method_decorator()`` to
        the view class by specifying the name of the method to decorate with the ``name`` arg of ``method_decorator()``.
        (django>=1.9)

        .. code-block:: python

            @method_decorator(legacy_decorator, name='dispatch')
            class ViewClass(View):
                ...

    2.  Putting the overridden decorated method into a mixin class that can be added to the base class list of a class
        based view and can optionally be parametrized through class attributes. This way you make the possibly ugly
        override + decoration only once in the mixin and then you reuse the mixin several times.

        This mixin technique can also be used without/instead of a decorator because the decorator logic can be put
        directly into the overridden method of the mixin class.

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
