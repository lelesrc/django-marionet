# -*- coding: utf-8 -*-
#

# django imports
from django.template import RequestContext
from django.test import TestCase

import portlets.utils

from urlparse import urlparse, urlunparse, urlunsplit, urljoin
from cgi import parse_qs
from urllib import quote, unquote

from marionet import log
from marionet.models import *
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)


class PortletURLTestCase(TestCase):

    def test_render_url__no_href(self):
        href = None
        params = {}
        method = 'GET'
        namespace = '__portlet__'
        location = 'http://testserver:80/page/1'
        query = parse_qs(location)
        render_url = PortletURL.render_url(
            location = urlparse(location),
            query = query,
            namespace = namespace,
            href = href,
            params = params,
            method = method,
            )
        self.assertEqual(render_url(), location)

    def test_render_url__get1(self):
        """ render GET
        """
        href = 'http://testserver:3000/test/target'
        params = {}
        method = 'GET'
        namespace = '__portlet__'
        location = 'http://testserver:80/page/1'
        query = parse_qs(location)
        render_url = PortletURL.render_url(
            location = urlparse(location),
            query = query,
            namespace = namespace,
            href = href,
            params = params,
            method = method,
            )
        self.assertEqual(render_url(),
             'http://testserver:80/page/1?__portlet___href=http%3A//testserver%3A3000/test/target')

    def test_render_url__get2(self):
        """ render GET with 2 portlets
        """
        pass

    def test_render_url__post(self):
        """ render POST
        """
        href = 'target'
        params = {'foo': 'bar'}
        method = 'POST'
        namespace = '__portlet__'
        location = 'http://testserver:80/page/1'
        query = parse_qs(location)
        pu = PortletURL.render_url(
            location = urlparse(location),
            query = query,
            namespace = namespace,
            href = href,
            params = params,
            method = method,
            )
        self.assert_(pu)
        #print pu
        #self.assertEqual('TODO', location+'?__portlet___href=target')
