# -*- coding: utf-8 -*-
#

# django imports
from django.test import TestCase

import signal

from PyQt4.QtCore import SIGNAL, QUrl
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import *

from BeautifulSoup import BeautifulSoup

from marionet import log
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

# the application instance - one for all tests
QT_APP = QApplication([])


class XHRTestCase(TestCase):

    def setUp(self):
        # Ctrl-C halts the test suite
        signal.signal( signal.SIGINT, signal.SIG_DFL )


    def test_javascript(self):
        page = QWebPage()
        page.mainFrame().setHtml("""
<html>
  <head>
  <script type="text/javascript">
  document.write("Hello World!");
  </script>
  </head>
  <body></body>
</html>
        """)
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)


    def test_jquery(self):
        page = QWebPage()
        page.mainFrame().setHtml("""
<html>
  <head>
  <script type="text/javascript" src="/media/js/jquery-1.4.2.min.js"></script>
  </head>
  <body></body>
  <script type="text/javascript">
  if(jQuery) {
      $("body").html('Hello World!');
  }
  </script>
</html>
        """, QUrl( 'http://localhost:8000' ))
        # connect the signal to quit the application after the page is loaded
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), lambda x: QT_APP.quit() )
        QT_APP.exec_() # start the application to load external JS
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)

