# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet import log
from marionet.models import WebClient, PageProcessor
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

import inspect
#import libxml2
#from copy import copy


class ResponseMock():
    def __init__(self,body,head=None):
        self.head = head
        self.body = body

    def read(self):
        return self.body


class PageProcessorTestCase(TestCase):
    def setUp(self):
        self.junit_url = 'http://localhost:3000/caterpillar/test_bench/junit'

    def test_transform(self):
        """ Simple GET.
        """
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_simple')
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)        
        self.assert_(tree)
        #print tree
        # now the very test
        out = PageProcessor.transform(tree,'body')
        #print out

    def test_parse_tree(self):
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_simple')
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)
        self.assert_(tree)
        #print tree
        #print inspect(tree)

    def test_process(self):
        """ Response processing chain.
        """
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_simple')
        self.assertEqual(200, response.status)
        (out,meta) = PageProcessor.process(response)
        self.assert_(out)
        self.assert_(meta)

    def test_title_ok(self):
        """ Response metadata.
        """
        html = '''
<html>
  <head>
    <title>
      Portlet title
    </title>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8"></meta>
  </head>
</html>
            '''
        response = ResponseMock(body=html)
        self.assert_(response)
        (out,meta) = PageProcessor.process(response)
        self.assert_(out)
        self.assert_(meta)
        self.assertEqual('Portlet title',meta['title'])

    def test_title_bad(self):
        """ Response metadata.
        """
        html = '''
<html>
  <head>
  </head>
</html>
            '''
        response = ResponseMock(body=html)
        self.assert_(response)
        (out,meta) = PageProcessor.process(response)
        self.assert_(out)
        self.assert_(meta)
        self.assertEqual('',meta['title'])

    def test_images(self):
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_images')
        self.assertEqual(200, response.status)
        (out,meta) = PageProcessor.process(response)
        self.assert_(out)
        print out


