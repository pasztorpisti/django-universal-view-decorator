import logging

import mock
from django.test import TestCase
from django.views.generic import View

from django_universal_view_decorator.decorators import view_class_decorator


class TestViewClassDecoratorDebugLog(TestCase):
    def setUp(self):
        self.orig_level = view_class_decorator.logger.level
        view_class_decorator.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        view_class_decorator.logger.setLevel(self.orig_level)

    @mock.patch.object(view_class_decorator.logger, 'debug')
    def test_class_decoration_logs_twice(self, mock_debug):
        def my_decorator(view):
            return view

        @view_class_decorator.view_class_decorator(my_decorator)
        class ViewClass(View):
            pass

        self.assertEqual(mock_debug.call_count, 2)
        self.assertEqual(mock_debug.mock_calls[0][1][0],
                         'Before decorating %(cls)r with %(decorators)r it already has decorators %(accumulated)r')
        self.assertEqual(mock_debug.mock_calls[1][1][0],
                         'After decorating %(cls)r with %(decorators)r it has decorators %(accumulated)r')
