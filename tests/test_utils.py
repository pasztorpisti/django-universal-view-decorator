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
