# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.template import RequestContext
from django.test import TestCase

import sys
import signal
import traceback
 
from optparse import OptionParser
#from PySide.QtCore import *
#from PyQt4.QtCore import SIGNAL, QUrl
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import *

import urllib2
from BeautifulSoup import BeautifulSoup

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


class XHRTestCase(TestCase):

    def setUp(self):
        self.app = QApplication([])

    def test_QWebPage(self):
        page = QWebPage()
        page.mainFrame().setHtml("""
<html><head>
<script type="text/javascript">
document.write("Hello World!");
</script>
</head><body>
</body></html>
        """)
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)


