from django.test import TestCase
from django_universal_view_decorator.utils import class_property


class TestClassProperty(TestCase):
    class MyClass(object):
        @class_property
        def my_class_property(cls):
            return cls, 'class_property'

    def test_with_class(self):
        self.assertEqual(self.MyClass.my_class_property, (self.MyClass, 'class_property'))

    def test_with_instance(self):
        self.assertEqual(self.MyClass().my_class_property, (self.MyClass, 'class_property'))

    def test_using_getter(self):
        class MyClass(object):
            my_class_property = class_property()

            @my_class_property.getter
            def could_be_my_class_property_but_it_isnt_because_of_testing(cls):
                return cls, 'class_property'

        self.assertEqual(MyClass.my_class_property, (MyClass, 'class_property'))
        self.assertEqual(MyClass.could_be_my_class_property_but_it_isnt_because_of_testing, (MyClass, 'class_property'))
