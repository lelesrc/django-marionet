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

class WebClientTestCase(TestCase):
    """ Please note that the 'portlet test bench' from Caterpillar project
    needs to be running while running these tests.

    Get the 'example' Rails app from http://github.com/lamikae/rails-portlet
    or roll your own by following instructions at http://github.com/lamikae/caterpillar
    """
    def setUp(self):
        self.junit_url = 'http://localhost:3000/caterpillar/test_bench/junit'

    def test_get(self):
        """ Simple GET.
        """
        client = WebClient()
        self.assert_(client)
        response = client.get(url=self.junit_url)
        self.assertEqual(200, response.status)
        self.assertEqual(0, len(client.cookies))

    def test_get_cookie(self):
        """ Cookie and session test.
        """

        client = WebClient()
        self.assert_(client)
        session_id = None
        url = self.junit_url+'/session_cookie'

        response = client.get(url=url)
        self.assertEqual(200, response.status)
        cookies = client.cookies
        self.assertEqual(1, len(cookies))

        xml = response.read()
        doc = libxml2.parseDoc(xml)
        self.assert_(doc)
        nodes = doc.xpathEval('//id/text()')
        self.assertEqual(1, len(nodes))
        session_id = nodes[0].content
        self.assert_(session_id)

        # GET again and assert that the session remains the same
        xml = doc = nodes = response = None
        client = WebClient()
        self.assert_(client)
        self.assertEqual(0, len(client.cookies))
        client.cookies = cookies
        self.assertEqual(1, len(client.cookies))

        response = client.get(url=url)
        self.assertEqual(200, response.status)
        cookies = client.cookies
        self.assertEqual(1, len(cookies))

        xml = response.read()
        doc = libxml2.parseDoc(xml)
        self.assert_(doc)
        nodes = doc.xpathEval('//id/text()')
        self.assertEqual(1, len(nodes))
        _session_id = nodes[0].content
        self.assert_(_session_id)

        self.assertEqual(session_id,_session_id)


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

