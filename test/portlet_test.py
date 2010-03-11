# -*- coding: utf-8 -*-
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

    def test_foo(self):
        pass
