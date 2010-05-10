# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.auth.models import User
from django.template import RequestContext
from django.test import TestCase

import portlets.utils

from marionet import context_processors
from marionet.models import *
from marionet.tests.utils import RequestFactory


class ContextProcessorsTestCase(TestCase):

    def test_render_context_processor_get(self):
        """ Context preprocessor GET
        """
        path = '/page/1'
        query = {'foo': 'bar'}
        request = RequestFactory().get(path, query)
        context = RequestContext(request, [context_processors.render_ctx])

        location = context.get('location')
        self.assertEqual(location.scheme, 'http')
        self.assertEqual(location.netloc, 'testserver:80')
        self.assertEqual(location.path, path)
        
        self.assertEqual('foo=bar', context.get('query').urlencode())
        self.assertEqual('', context.get('post').urlencode())

    def test_render_context_processor_post(self):
        """ Context preprocessor POST
        """
        path = '/page/1'
        query = path + '?foo=bar'
        params = {'record_id': '420'}
        request = RequestFactory().post(query, params)
        context = RequestContext(request, [context_processors.render_ctx])

        location = context.get('location')
        self.assertEqual(location.scheme, 'http')
        self.assertEqual(location.netloc, 'testserver:80')
        self.assertEqual(location.path, path)
        
        self.assertEqual('foo=bar', context.get('query').urlencode())
        self.assertEqual('record_id=420', context.get('post').urlencode())

