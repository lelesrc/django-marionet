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

class MarionetTestCase(TestCase):

    def setUp(self):
        pass

    def test_defaults(self):
        """
        """
        return
        mn_portlet = Marionet() # no database object creation
        self.assert_(mn_portlet)
        self.assertEqual("help",mn_portlet.name)
        #self.assertEqual("marionet/help.html",mn_portlet.route)
        self.assertNotEqual(None,mn_portlet.render())

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

