# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet import log
from marionet.models import WebClient, XSLTransformation
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

#import inspect
#import libxml2
#from copy import copy

class XSLTransformationTestCase(TestCase):
    def setUp(self):
        self.junit_url = 'http://localhost:3000/caterpillar/test_bench/junit'

    def test_simple(self):
        """ Simple GET.
        """
        client = WebClient()
        self.assert_(client)
        response = client.get(self.junit_url+'/xslt_simple')
        self.assertEqual(200, response.status)
        html = response.read()
        #print body
        out = XSLTransformation.transform(html,'body')
        #print out

