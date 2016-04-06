import json

from django.core.urlresolvers import reverse
from django.test import TestCase, Client


class TestResponses(TestCase):
    def test_regular_view_function(self):
        client = Client()
        response = client.get(reverse('regular_view_function', args=[0]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertDictContainsSubset(dict(
            responder='regular_view_function',
            number=1,
        ), data)

    def test_view_class(self):
        client = Client()
        response = client.get(reverse('view_class', args=[0]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertDictContainsSubset(dict(
            responder='ViewClass',
            number=0,
        ), data)

    def test_view_subclass(self):
        client = Client()
        response = client.get(reverse('view_subclass', args=[0]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertDictContainsSubset(dict(
            responder='ViewSubclass',
            number=0,
        ), data)

    def test_view_subclass2(self):
        client = Client()
        response = client.get(reverse('view_subclass2', args=[0]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertDictContainsSubset(dict(
            responder='ViewSubclass2',
            number=-10,
        ), data)
