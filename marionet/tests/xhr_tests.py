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

class Crawler( QWebPage ):
    def __init__(self, url):
        QWebPage.__init__( self )
        self._url = url
        self._html = None

    def crawl( self ):
        signal.signal( signal.SIGINT, signal.SIG_DFL )
        self.connect( self, SIGNAL( 'loadFinished(bool)' ), self._finished_loading )
        self.mainFrame().load( QUrl( self._url ) )

    def _finished_loading( self, result ):
        self._html = self.mainFrame().toHtml()
        QT_APP.quit() # quit the application, so the tests don't hang


class XHRTestCase(TestCase):

    def test_javascript(self):
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

    def test_jquery(self):
        crawler = Crawler( 'http://localhost:8000/jquery' )
        crawler.crawl()
        QT_APP.exec_() # start the application
        html = crawler._html
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)

