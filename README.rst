===============================
django-universal-view-decorator
===============================

.. contents::

------------
Introduction
------------

In django you can implement views in two different standard ways (regular view function, class based view) and the same
project can make use of both techniques in parallel. In case of class based views I've seen several ways of decorating
the view. Sometimes the effect of these decoration techniques is a little bit different and all of them have their use.
With this library I'm introducing just another way to decorate view classes along with a unified way to implement
view decorators that work the same way on regular view functions, view classes, and also on view class methods. Before
describing my solution let's list the most popular widely used view decoration techniques.

----------------------------------
Popular view decoration techniques
----------------------------------

Regular view functions
......................

Decorating a regular view function if fairly straightforward:

1.  You either simply apply the decorator to the regular view function...
2.  or you apply the decorator only on a per-url basis in your url config when you attach the view function to a
    specific url.

.. code-block:: python

    # 1.
    @my_decorator
    def my_regular_view_function(request):
        ...


    # 2.
    urlpatterns = [
        url(r'^my/url/$', my_decorator(views.my_regular_view_function)),
        ...
    ]


Class based views
.................

In case of class based views things are a bit more complicated. I've seen quite a few ways of decorating a class based
view:

1.  On a per-url basis in the url config when the class based view gets converted to a regular view function (by calling
    its `as_view()` class method).
2.  By overriding its `dispatch()` method or one of the http-request-method specific methods called by `dispatch()`
    and decorating the method (usually with the help of `django.utils.decorators.method_decorator()`).
3.  The previous method decoration technique sometimes overrides a method (e.g.: `dispatch()`) just for the sake of
    decorating it. The implementation of the method in those cases simply calls the `super()` version. This is quite an
    ugly non-pythonic way that has two beautified versions:

    1.  You can apply your decorator to the method by using the `django.utils.decorators.method_decorator()` on the view
        class by specifying the name of the method to decorate with the `name` arg of `method_decorator()`.
        (django>=1.9)
    2.  Putting the overridden decorated method into a mixin class that can be added to the base class list of a class
        based view and can optionally be parametrized through class attributes. This mixin technique can be used
        without/instead of a decorator because the decorator logic can be put directly into the overridden method of
        the mixin class.

.. code-block:: python

    # 1.
    urlpatterns = [
        url(r'^my/url/$', my_decorator(views.MyClassBasedView.as_view())),
        ...
    ]


    # 2.
    class MyClassBasedView(View):
        @method_decorator(my_decorator)
        def dispatch(self, request, *args, **kwargs):
            # We overridden this method without adding logic: this is super UGLY!
            return super().dispatch(request, *args, **kwargs)

        @method_decorator(my_decorator_2)
        def get(self, request):
            ...


    # 3.1.
    @method_decorator(my_decorator, name='dispatch')
    class MyClassBasedView(View):
        ...


    # 3.2.
    class MyDecoratorMixin(object):
        """ Reusable mixin for class based views. """
        @method_decorator(my_decorator)
        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)


    class MyDecoratorMixin2(object):
        """ Reusable mixin for class based views. """
        def get(self, request, *args, **kwargs):
            # In this case we haven't actually used a decorator,
            # we put the decorator logic directly to this method.
            # TODO: manipulate input args if you want
            response = super().get(request, *args, **kwargs)
            # TODO: manipulate the response if you want
            return response


    class MyClassBasedView(MyDecoratorMixin, MyDecoratorMixin2, View):
        ...


---------------------------------------------------
View decoration techniques provided by this library
---------------------------------------------------

This library has two features to offer:

1.  A `universal_view_decorator()` that works similarly to the `django.utils.decorators.method_decorator()` but it works
    on regular view functions, view class methods, and view classes too with the same syntax however it has different
    behavior when used to decorate a view class. This difference is very important and discussed later in this doc.
2.  Implementing view decorators in an object oriented way.

    1.  If you implement your view decorator this way then you can use object oriented features (like inheritance) in
        the implementation of your view decorators plus as a bonus your view decorator automatically works with regular
        view functions, view classes, and view class methods without any helpers like
        `django.utils.decorators.method_decorator()` or my `universal_view_decorator()` (that has been provided for easy
        reuse of existing simple view decorators).
    2.  If your view decorator has only optional arguments then this view decorator implementation allows you to use
        the decorator without writing the empty parents `()` after your decorator when you don't pass any arguments.

.. code-block:: python

    # 1.
    from django_universal_view_decorator import universal_view_decorator


    @universal_view_decorator(my_legacy_decorator(decorator_param))
    def regular_view_function(request):
        ...


    @universal_view_decorator(my_legacy_decorator(decorator_param), my_legacy_decorator_2)
    class ViewClass(View):
        ...


    class ViewClass(View):
        @universal_view_decorator(my_legacy_function_decorator)
        def get(self, request):
            ...


    # 2.
    from django_universal_view_decorator import ViewDecoratorBase


    class MyViewDecorator(ViewDecoratorBase):
        def __init__(self, my_decorator_arg=5):
            super(MyViewDecorator, self).__init__()
            self.my_decorator_arg = my_decorator_arg

        def _call_view_function(self, decoration_instance, view_class_instance, view_function, *args, **kwargs):
            # Note: You can use `self.my_decorator_arg` here.

            # If you need the request arg and you know that in case of view class
            # method decoration your decorated view methods always have a request arg.
            request = args[0]
            test = self._perform_test(*args)
            # TODO: manipulate the request and/or return a response instead of calling
            # the decorated view function if that is what you want.
            response = view_function(*args, **kwargs)
            # TODO: manipulate the response or forge a new one before returning it.
            return response

        def _perform_test(self, *args):
            return True


    class MyViewDecoratorSubclass(MyViewDecorator):
        def _perform_test(self, *args):
            return False

    my_view_decorator = MyViewDecorator.universal_decorator
    my_view_decorator_subclass = MyViewDecoratorSubclass.universal_decorator


    # 2.1.
    @my_view_decorator()
    def regular_view_function(request):
        ...


    class ViewClass(View):
        @my_view_decorator(6)
        def get(self, request):
            ...


    @my_view_decorator_subclass(my_decorator_arg=7)
    class ViewClass(View):
        ...

    # 2.2.
    @my_view_decorator      # <- No need for `()` after `@my_view_decorator`
    def regular_view_function(request):
        ...
