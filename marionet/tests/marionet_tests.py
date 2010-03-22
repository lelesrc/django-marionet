# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.template import RequestContext
from django.test import TestCase

# reviews imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot
import portlets.utils

from marionet import log
from marionet.models import Marionet, PortletFilter
from marionet.models import WebClient
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

import inspect
import libxml2
from copy import copy


class WebClientTestCase(TestCase):
    """ Please note that the 'portlet test bench' from Caterpillar project
    needs to be running while running these tests.

    Get the 'example' Rails app from http://github.com/lamikae/rails-portlet
    or roll your own by following instructions at http://github.com/lamikae/caterpillar
    """
    def setUp(self):
        self.junit_url = 'http://localhost:3000/caterpillar/test_bench/junit'

    def tearDown(self):
        pass

    def test_get(self):
        """ Simple GET.
        """
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        response = client.get(self.junit_url)
        self.assertEqual(200, response.status)
        self.assertEqual(0, len(client.cookies))

    def test_get_cookie(self):
        """ Cookie and session test.
        """
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        session_id = None
        url = self.junit_url+'/session_cookie'

        response = client.get(url)
        self.assertEqual(200, response.status)
        cookies = copy(client.cookies)
        self.assertEqual(1, len(cookies))

        xml = response.read()
        doc = libxml2.parseDoc(xml)
        self.assert_(doc)
        nodes = doc.xpathEval('//id/text()')
        self.assertEqual(1, len(nodes))
        session_id = nodes[0].content
        self.assert_(session_id)

        # GET again and assert that the session remains the same
        xml = doc = nodes = response = client = None
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        client.add_cookies(cookies)
        self.assertEqual(1, len(client.cookies))

        response = client.get(url)
        self.assertEqual(200, response.status)
        self.assertEqual(1, len(client.cookies))

        xml = response.read()
        doc = libxml2.parseDoc(xml)
        self.assert_(doc)
        nodes = doc.xpathEval('//id/text()')
        self.assertEqual(1, len(nodes))
        _session_id = nodes[0].content
        self.assert_(_session_id)

        self.assertEqual(session_id,_session_id)

    def test_post_redirect(self):
        """ Test POST + redirect.
        """
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        url = self.junit_url+'/post_redirect_get'
        response = client.post(url)
        self.assertEqual(200, response.status)
        self.assertEqual(0, len(client.cookies))
        self.assertEqual(
            '/caterpillar/test_bench/junit/redirect_target',
            response.read())

    def test_post_params(self):
        """ Test POST + params.
        """
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        url = self.junit_url+'/post_params'
        params = {'foo': 'bar', 'baz': 'xyz'}
        response = client.post(url,params=params)
        self.assertEqual(200, response.status)
        self.assertEqual(0, len(client.cookies))
        xml = response.read()
        doc = libxml2.parseDoc(xml)
        for (k,v) in params.items():
            n = doc.xpathEval('//'+k)
            self.assert_(n)
            self.assertEqual(v,n[0].content)

    def test_post_cookies(self):
        """ Test POST redirect + preset cookies.
        """
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        url = self.junit_url+'/post_cookies'
        cookies = {'foo': ['foo=bar'], 'baz': ['baz=xyz']}
        client.add_cookies(cookies)

        response = client.post(url)
        self.assertEqual(200, response.status)
        # server adds a third cookie at redirect
        self.assertEqual(3, len(client.cookies))
        xml = response.read()
        #print xml
        doc = libxml2.parseDoc(xml)
        for _c in cookies.values():
            (k,v) = _c[0].split('=')
            n = doc.xpathEval('//'+k)
            self.assert_(n)
            self.assertEqual(v,n[0].content)

    def test_server_cookies(self):
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        url = self.junit_url+'/foobarcookies'
        response = client.post(url)
        self.assertEqual(200, response.status)
        # server sends three cookies
        self.assertEqual(3, len(client.cookies))

        # then head to a new url
        url = self.junit_url+'/foobarcookiestxt'
        response = client.post(url)
        self.assertEqual(200, response.status)
        self.assertEqual('__g00d____yrcl____3ver__',response.read())

    def test_sanity(self):
        """ 
        """
        client_1 = WebClient()
        self.assert_(client_1)
        self.assertEqual(0, len(client_1.cookies))
        cookies = {'foo': ['foo=bar'], 'baz': ['baz=xyz']}
        client_1.cookies = copy(cookies)
        self.assertEqual(2, len(client_1.cookies))

        client_2 = WebClient()
        self.assert_(client_2)
        self.assertEqual(0, len(client_2.cookies))
        cookies = {
            'foo': ['foo=abc'],
            'bar': ['bar=def'],
            'baz': ['baz=ghi'],
            }
        client_2.cookies = copy(cookies)
        self.assertEqual(3, len(client_2.cookies))
        self.assertEqual(2, len(client_1.cookies))


class MarionetTestCase(TestCase):

    def setUp(self):
        self.session_secret='xxx'

    def test_defaults(self):
        """
        """
        mn_portlet = Marionet()
        self.assert_(mn_portlet)
        self.assertEqual(None,mn_portlet.session_secret)
        out = mn_portlet.render() # calls filter + changes state!
        self.assertNotEqual(None,out)

    def test_secret(self):
        """
        """
        mn_portlet = Marionet(session_secret=self.session_secret)
        self.assert_(mn_portlet)
        self.assertEqual(self.session_secret,mn_portlet.session_secret)
        out = mn_portlet.render() # calls filter + changes state!
        self.assertNotEqual(None,out)

    def test_portlet_filter(self):
        """Portlet Filter.
        """
        request = RequestFactory().get('/FOOBAR')
        ctx = RequestContext(request, {})

        # define a method that acts like Portlet methods
        def test_method(self,ctx):
            return "" # return String

        # the method chain consists of the filter and the view method
        method_chain = PortletFilter.render_filter(test_method)
        self.assert_(method_chain)
        # run the chain
        response = method_chain(ctx)
        # the object is still resident in memory, maintaining state
        self.assertNotEqual(None,response)
        #print response

