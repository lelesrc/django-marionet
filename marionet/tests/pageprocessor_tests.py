# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet import log
from marionet.models import Marionet, WebClient, PageProcessor
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

from lxml import etree
from BeautifulSoup import BeautifulSoup

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
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'

    def test_transform(self):
        """ Simple GET.
        """
        url = self.junit_url+'/xslt_simple'
        portlet = Marionet(url=url)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(portlet,response)
        self.assert_(tree)
        #print tree
        # now the very test
        out = PageProcessor.transform(tree,'body')
        #print out
        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        portlet_div = soup.find(id='%s_body' % portlet.namespace())
        self.assert_(portlet_div)
        #print portlet_div

    def test_parse_tree(self):
        url = self.junit_url+'/xslt_simple'
        portlet = Marionet(url=url)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(portlet,response)
        self.assert_(tree)
        # test meta data
        portlet_tag = tree.find('head/portlet')
        self.assertEqual(etree._Element,portlet_tag.__class__)
        self.assertEqual(portlet.namespace(), portlet_tag.get('namespace'))
        self.assertEqual(self.junit_base, portlet_tag.get('baseUrl'))

    def test_process(self):
        """ Response processing chain.
        """
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_simple')
        self.assertEqual(200, response.status)
        (out,meta) = PageProcessor.process(None,response)
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
        (out,meta) = PageProcessor.process(None,response)
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
        (out,meta) = PageProcessor.process(None,response)
        self.assert_(out)
        self.assert_(meta)
        self.assertEqual('',meta['title'])

    def test_images(self):
        url = self.junit_url+'/xslt_images'
        portlet = Marionet(url=url)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        (out,meta) = PageProcessor.process(portlet,response)
        self.assert_(out)
        #print out


