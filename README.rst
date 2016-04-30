===============================
django-universal-view-decorator
===============================

Smart view class (CBV) decoration
"""""""""""""""""""""""""""""""""


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


About Class Based View (CBV) decoration
=======================================

In django you can implement views in two different ways:

1. FBV (Function Based View)
2. CBV (Class Based View)

A project can make use of both techniques in parallel. While decorators work really well with FBVs, using them
with CBVs is a bit uglier. The django documentation recommends two techniques to decorate class based views:

https://docs.djangoproject.com/en/1.9/topics/class-based-views/intro/#decorating-class-based-views

1. Decorating in URLConf: applying the decorator to the view function returned by the ``View.as_view()`` class method.

    .. code-block:: python

        urlpatterns = [
            url(r'^my_view/', permission_required('my_app.my_permission')(MyView.as_view())),
        ]

    I think this decoration technique is solid. It treats your view class as a view function and places the
    decorator between the url config and the view function exactly as in case of decorating a FBV. The decorator
    is guaranteed to execute before any methods in the decorated CBV.

    My only problem is that I have to do this in the URLConf module and on a per-url basis instead of being
    able to apply the decorator onto the view class in the module in which it has been implemented.

2. Applying your decorator to one of the methods of your view class (e.g.: ``dispatch()``) with the help of
   ``@django.utils.decorators.method_decorator``.

    .. code-block:: python

        class MyView(View):
            @method_decorator(permission_required('my_app.my_permission'))
            def dispatch(self, *args, **kwargs):
                return super(MyView, self).dispatch(*args, **kwargs)

        # django 1.9+: this way you don't have to override dispatch() just to be able to decorate it
        @method_decorator(permission_required('my_app.my_permission'), name='dispatch')
        class MyView(View):
            ...

    Problems with this solution:

    - If someone subclasses the view and overrides the decorated method then the method override in the subclass is
      executed before the decorator. The decorator can actually be bypassed completely by not calling the super
      version of the overridden method. This may be a desired behavior sometimes but in case of some critical
      (e.g.: permission) decorators it is a problem. In case of decorating in URLConf this isn't a problem: in
      that case the decorator is always executed before any view class methods.
    - Minor issue: I have to write ``@method_decorator(permission_required('my_app.my_permission'))`` instead of
      simply ``@permission_required('my_app.my_permission')``.


As you see the two decoration techniques have different behavior. I find the behavior of technique #1 (URLConf
decoration) more useful and robust while cosmetically I prefer applying decorators to my view class implementations
as in case of technique #2 (``@method_decorator``).

This library provides a ``@universal_view_decorator`` helper (similar to django's ``@method_decorator``) that combines
the behavior of decoration technique #1 with the cosmetics of technique #2:

- You can apply the decorator to the view class directly - you don't have to mess with URLConf unless you want to
  apply decorators on a per-url basis.
- Behaves like decoration method #1: under the hood it applies the decorator to the return value of
  ``View.as_view()`` so it can't be bypassed with subclassing.

Besides the previously listed features ``@universal_view_decorator`` provides a bit more convenient interface than
django's ``@method_decorator``: after wrapping your view decorator with this helper you can apply it to FBVs, CBVs
and CBV methods with the exact same syntax. There is also a ``@universal_view_decorator_with_args`` variant of this
helper that comes in handy with view decorators that have parameters.


Installation
============

.. code-block:: sh

    pip install django-universal-view-decorator

Alternatively you can download the distribution from the following places:

- https://pypi.python.org/pypi/django-universal-view-decorator#downloads
- https://github.com/pasztorpisti/django-universal-view-decorator/releases


Usage
=====


``@universal_view_decorator``
-----------------------------

If you wrap your view decorator with ``@universal_view_decorator`` then you can apply it to:

- FBVs (just like before wrapping it with ``@universal_view_decorator``)
- CBVs (with the same behavior as in case of decorating ``View.as_view()`` in URLConf)
- CBV methods (with the same behavior when applying your decorator to the view class method using django's
  ``@method_decorator``)


.. code-block:: python

    from django_universal_view_decorator import universal_view_decorator


    @universal_view_decorator(login_required)
    def function_based_view(request):
        ...


    # You can wrap multiple decorators at the same time
    @universal_view_decorator(login_required, permission_required('my_app.my_permission'))
    def function_based_view(request):
        ...


    # This double decoration is equivalent in behavior to the previous example
    # where we used one wrapper to wrap both legacy decorators.
    @universal_view_decorator(login_required)
    @universal_view_decorator(permission_required('my_app.my_permission'))
    def function_based_view(request):
        ...


    # Applying the decorator to view classes. Behavior is the same as applying
    # the permission decorator to ``ClassBasedView.as_view()`` in the URLConf.
    @universal_view_decorator(permission_required('my_app.my_permission'))
    class ClassBasedView(View):
        ...


    # Applying the decorator to view class methods.
    # Behavior is equivalent to that of django's @method_decorator.
    class ClassBasedView(View):
        @universal_view_decorator(login_required)
        def head(self, request):
            ...


    # Wrapping the decorator only once for reuse in our project:
    reusable_universal_login_required = universal_view_decorator(logic_required)


    @reusable_universal_login_required
    class ClassBasedView(View):
        ...


``@universal_view_decorator_with_args``
---------------------------------------

The ``@universal_view_decorator_with_args`` decorator is pretty much the same as ``@universal_view_decorator`` but
it allows you to parametrize the wrapped decorator *after* wrapping it. This is very useful if you want to wrap
a decorator only once for reuse but the decorator has parameters that you don't want to specify when you do the
wrapping:


.. code-block:: python

    from django_universal_view_decorator import universal_view_decorator,
                                                universal_view_decorator_with_args


    # with @universal_view_decorator you have to bind args before wrapping :-(
    my_permission_required = universal_view_decorator(permission_required('my_app.my_permission'))

    # we can specify args for permission_required when we apply the decorator :-)
    universal_permission_required = universal_view_decorator_with_args(permission_required)


    @universal_permission_required('my_app.my_permission')
    def function_based_view(request):
        ...


    @universal_permission_required('my_app.my_permission')
    class ClassBasedView(View):
        ...


    class ClassBasedView(View):
        @universal_permission_required('my_app.my_permission')
        def dispatch(self, request, *args, **kwargs):
            ...


Inheritance
===========

Subclasses of a decorated view class inherit the decorators. In the following example ``DerivedView`` inherits a
``@login_required`` decorator from its base class:


.. code-block:: python

    from django_universal_view_decorator import universal_view_decorator


    @universal_view_decorator(login_required)
    class BaseView(View):
        ...


    @universal_view_decorator(permission_required('my_app.my_permission'))
    class DerivedView(View):
        ...


The inherited base class decorators are applied first. The above example has the same effect on ``DerivedView``
as decorating it in a URLConf like this:


.. code-block:: python

    urlpatterns = [
        url(r'^derived_view/', permission_required('my_app.my_permission')(login_required(DerivedView.as_view()))),
    ]
