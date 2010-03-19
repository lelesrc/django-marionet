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
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

import inspect

class WebClientTestCase(TestCase):
    def setUp(self):
        self.junit_url = 'http://localhost:3000/caterpillar/test_bench/junit'

    def test_get(self):
        """ Java test:
        client = new OnlineClient(new URL(railsJUnitURL));
        assertNotNull(client);
        byte[] body = client.get();
        assertEquals(200,client.statusCode);
        assertEquals(0,client.cookies.length);
        """
        client = WebClient()
        self.assert_(client)
        (status_code, response) = client.get(url=self.junit_url)
        self.assertEqual(200, status_code)
        self.assertEqual(0, len(response.cookies()))

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

