# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet import log
from marionet.models import Marionet, PortletFilter
from marionet.models import WebClient
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

import inspect
import libxml2
from copy import copy

class XSLTransformerTestCase(TestCase):
    def setUp(self):
        pass

