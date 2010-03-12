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
log.setlevel('critical')

class MarionetTestCase(TestCase):

    def setUp(self):
        pass

    def test_defaults(self):
        """
        """
        mn_portlet = Marionet() # no database object creation
        self.assert_(mn_portlet)
        self.assertEqual("help",mn_portlet.name)
        self.assertEqual("marionet/help.html",mn_portlet.route)
