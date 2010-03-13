# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.test import TestCase

# reviews imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot
import portlets.utils

from marionet.models import Marionet
from marionet import log
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

class MarionetTestCase(TestCase):

    def setUp(self):
        pass

    def test_defaults(self):
        """
        """
        mn_portlet = Marionet() # no database object creation
        self.assert_(mn_portlet)
        self.assertEqual("help",mn_portlet.name)
        #self.assertEqual("marionet/help.html",mn_portlet.route)
        self.assertNotEqual(None,mn_portlet.render())

    def test_filter(self):
        """ Filter is not instantiated, this is not Java.
        It is the __call__ method of Marionet.
        """
        mn_portlet = Marionet()
        self.assert_(mn_portlet)
