# -*- coding: utf-8 -*-
#

# django imports
from django.test import TestCase

import signal

from PyQt4.QtCore import SIGNAL, QObject, QUrl, QString, QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import *

from BeautifulSoup import BeautifulSoup

from marionet import log
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

# the application instance - one for all tests
QT_APP = QApplication([])


def evaluateJavaScript(frame, script):
    """
    Evaluates JavaScript on QWebFrame and exits to QApplication
    to get on with the unit test.
    """
    # start timer to kill QApplication
    timer = QTimer()
    QObject.connect(timer, SIGNAL( 'timeout()' ), QT_APP.quit)
    timer.start(200) # msec
    # apply XHR link click
    frame.evaluateJavaScript(QString(script))
    # execute the injected JavaScript
    QT_APP.exec_()


class XHRTestCase(TestCase):

    def setUp(self):
        # Ctrl-C halts the test suite
        signal.signal( signal.SIGINT, signal.SIG_DFL )
        self.xUnit_url = 'http://localhost:3000/caterpillar/test_bench/junit/'


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
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        QT_APP.exec_() # start the application to load external JS
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)


    def test_xhr_get(self):
        pass


    def test_xhr_post(self):
        """
        'Click' a link by JavaScript on a web page,
        this sends an XHR POST that updated the page with 'Hello World!'.

        See http://github.com/lamikae/caterpillar/blob/master/portlet_test_bench/helpers/caterpillar/application_helper.rb
        """
        page = QWebPage()
        page.mainFrame().load(QUrl( self.xUnit_url + 'xhr' ))
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        QT_APP.exec_() # load

        evaluateJavaScript(page.mainFrame(), """
            $('xhr_post').next().commit.click(); // next() is a way to say "input tag"
        """)

        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(str(html))
        self.assertEquals('Hello World!',soup.find(id='post_resp').text)
