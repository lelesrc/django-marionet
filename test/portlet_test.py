# -*- coding: utf-8 -*-
#
# Test cases copied from django-portlets (BSD license)
# author: diefenbach
#

import unittest

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

class PortletTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_slot(self):
        """
        """
        slot = Slot.objects.create(name="Left")
        self.assertEqual(slot.name, "Left")

    def test_portlet_registration(self):
        """
        """
        portlet_registration = PortletRegistration.objects.create(
            type = "textportlet",
            name = "TextPortlet",
        )

        self.assertEqual(portlet_registration.type, "textportlet")
        self.assertEqual(portlet_registration.name, "TextPortlet")
        self.assertEqual(portlet_registration.active, True)

        # try to add another portlet with same type or name
        self.assertRaises(IntegrityError, PortletRegistration.objects.create, type = "textportlet")
        self.assertRaises(IntegrityError, PortletRegistration.objects.create, name = "TextPortlet")

        # add another portlet with other name
        portlet_registration_2 = PortletRegistration.objects.create(
            type = "textportlet_2",
            name = "TextPortlet_2",
        )

    def test_portlet_assignment(self):
        """
        """
        slot = Slot.objects.create(name="Left")
        page = FlatPage.objects.create(url="/test/", title="Test")
        portlet = TextPortlet.objects.create(title="Text")

        portlet_assignment = PortletAssignment.objects.create(
            slot = slot,
            content = page,
            portlet = portlet,
        )

        self.assertEqual(portlet_assignment.slot, slot)
        self.assertEqual(portlet_assignment.content, page)
        self.assertEqual(portlet_assignment.portlet, portlet)

    def test_portlet_blocking(self):
        """
        """
        slot = Slot.objects.create(name="Left")
        page = FlatPage.objects.create(url="/test/", title="Test")

        portlet_blocking = PortletBlocking.objects.create(
            slot = slot,
            content = page,
        )

        self.assertEqual(portlet_blocking.slot, slot)
        self.assertEqual(portlet_blocking.content, page)

