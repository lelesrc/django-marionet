# -*- coding: utf-8 -*-

from django.test import TestCase
from django.template import RequestContext
import signal

from PyQt4.QtCore import SIGNAL, QObject, QUrl, QString, QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import *

from marionet import context_processors
from marionet.models import Marionet
from marionet.tests.utils import RequestFactory

from BeautifulSoup import BeautifulSoup


# the application instance - one for all tests
QT_APP = QApplication([])


class XHRTestCase(TestCase):

    def setUp(self):
        """
        Requires the Portlet test bench packaged with Caterpillar.

        See http://github.com/lamikae/caterpillar/blob/master/portlet_test_bench/helpers/caterpillar/junit_helper.rb
        """
        # Ctrl-C halts the test suite
        signal.signal( signal.SIGINT, signal.SIG_DFL )
        self.xUnit_url = 'http://localhost:3000/caterpillar/test_bench/junit/'

    def tearDown(self):
        QT_APP.quit

    def test_javascript(self):
        """
        Simple test for validating QWebFrame's reaction.
        """
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
        """ External JavaScript library and QWebPage.

        Test for running an external JavaScript library.
        jQuery is used to do a simple page update.
        """
        page = QWebPage()
        page.mainFrame().setHtml("""
        <html>
          <head>
          <script type="text/javascript" src="/javascripts/jquery-1.4.2.min.js"></script>
          </head>
          <body></body>
          <script type="text/javascript">
          if(jQuery) {
              $("body").html('Hello World!');
          }
          </script>
        </html>
        """, QUrl( 'http://localhost:3000' ))
        # connect the signal to quit the application after the page is loaded
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        # start the application to load external JS
        QT_APP.exec_()
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        self.assertEquals('Hello World!',soup.body.text)


    def test_xhr_onclick_post(self):
        """
        Launch a click event on an input element which sends an XHR POST that updates the page.
        """
        page = QWebPage()
        page.mainFrame().load(QUrl( self.xUnit_url + 'xhr' ))
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        QT_APP.exec_()
        # launch onClick
        evaluateJavaScript(page.mainFrame(), """
        $$('#xhr_onclick input').first().click();
        """)
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(str(html))
        self.assertEquals('Hello World!',soup.find(id='onclick_resp').text)


    def test_xhr_form_post(self):
        """
        Submit a form which sends an XHR POST that updates the page.
        """
        page = QWebPage()
        page.mainFrame().load(QUrl( self.xUnit_url + 'xhr' ))
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        QT_APP.exec_()
        # submit form
        evaluateJavaScript(page.mainFrame(), """
        $$('#xhr_form form').first().commit.click();
        """)
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(str(html))
        self.assertEquals('Hello World!',soup.find(id='form_resp').text)

    def test_marionet_xhr_form_post(self):
        self.fail('hangs test suite')
        portlet = Marionet.objects.create(url=self.xUnit_url + 'form',session=True)
        path = '/page/1'
        request = RequestFactory().get(path)
        context = RequestContext(request, [context_processors.render_ctx])
        portlet_render = portlet.render(context)
        print portlet_render

        page = QWebPage()
        page.mainFrame().setHtml("""
        <html>
          <head>
          <script type="text/javascript" src="/javascripts/jquery-1.4.2.min.js"></script>
          </head>
          <body>
          %s
          </body>
        </html>
        """ % portlet_render, QUrl( 'http://localhost:3000' ))
        # connect the signal to quit the application after the page is loaded
        page.connect( page, SIGNAL( 'loadFinished(bool)' ), QT_APP.quit )
        # start the application to load external JS
        QT_APP.exec_()
        # submit form
        evaluateJavaScript(page.mainFrame(), """
        $$('#ordinary_post form').first().commit.click();
        """)
        html = page.mainFrame().toHtml()
        soup = BeautifulSoup(html)
        #print soup.html
        self.fail('http://testserver:80/ does not respond to submit')


def evaluateJavaScript(frame, script):
    """
    Evaluates JavaScript on QWebFrame and exits to QApplication
    to get on with the unit test.
    """
    # start timer to kill QApplication
    timer = QTimer()
    QObject.connect(timer, SIGNAL( 'timeout()' ), QT_APP.quit)
    timer.start(200) # msec
    # inject JavaScript
    frame.evaluateJavaScript(QString(script))
    # execute app, which the timer will kill
    QT_APP.exec_()


