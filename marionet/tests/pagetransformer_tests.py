# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet.models import PageTransformer, MarionetSession
from marionet.tests.utils import RequestFactory

from lxml import etree
from BeautifulSoup import BeautifulSoup
import re
from urlparse import urljoin


class ResponseMock():
    def __init__(self,body,head=None):
        self.head = head
        self.body = body

    def read(self):
        return self.body


class PageTransformerTestCase(TestCase):
    def setUp(self):
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'

    def test_link(self):
        anchor = [etree.fromstring('<a href="/caterpillar/test_bench">Link text</a>')]
        session = MarionetSession.objects.create(
            url = self.junit_url
            )
        ctx_location = 'http://example.com:8000/some-page'
        session.set('location', ctx_location)

        link = PageTransformer.link(None,
            anchor,
            [session]
            )[0] # take 1st _Element
        self.assertEqual(
            link.get('href'),
            ctx_location+'?'+
                session.get('namespace')+
                '.href=http%3A//localhost%3A3000/caterpillar/test_bench')

        ## with baseurl

        session.set('baseURL', 'http://some-other:3000/')
        link = PageTransformer.link(None,
            anchor,
            [session]
            )[0] # take 1st _Element
        print(link.get('href'))
        print(ctx_location+'?'+
                session.get('namespace')+
                '.href=http%3A//localhost%3A3000/caterpillar/test_bench')
        #return
        self.assertEqual(
            link.get('href'),
            ctx_location + '?'+
                session.get('namespace')+
                '.href=http%3A//some-other%3A3000/caterpillar/test_bench')
        #print etree.tostring(link)

    def test_form(self):
        form = [etree.fromstring("""
            <form action="/caterpillar/test_bench/http_methods/post" method="post">
              <p>
                <span>Input text:</span>
                <input id="msg" name="msg" size="42" type="text" value="Python was conceived in the late 1980s and its implementation was started in December 1989 by Guido van Rossum" />
              </p>
            </form>
            """)]
        session = MarionetSession.objects.create(
            location = 'http://example.com:8000/some-page',
            query = '',
            base = self.junit_base,
            )

        _form = PageTransformer.form(None,
            form,
            [session]
            )[0] # take 1st _Element
        self.assertEqual(
            _form.get('action'),
            'http://example.com:8000/some-page?__portlet__.href=http%3A//localhost%3A3000/caterpillar/test_bench/http_methods/post&__portlet__.action=process')

    def test_new_Ajax(self):
        """
        To be specific, the goals of an end to end Ajax programming model for portlets were the following:

        * Allow state-changing requests (e.g. via an action URL) initiated via a client API
        * Support state changes via processAction
        * Provide first-class support for the new coordination models (i.e. events and shared/public render parameters) being introduced into JSR-286.
        * Provide a client API that is easy to migrate to, and can easily be plugged into various JavaScript frameworks.
        * Design the client API such that portals can consistently manage the UI and its state in the browser.

        @see http://www.subbu.org/blog/2007/08/update-on-jsr-286-and-ajax
        """
        """  
        <div xmlns="http://www.w3.org/1999/xhtml" id="xhr_onclick">
<input onclick="new Ajax.Updater('onclick_resp', '/caterpillar/test_bench/junit/xhr_hello', {asynchronous:true, evalScripts:true});" type="button" value="send o
nclick POST" /><div id="onclick_resp"></div>
</div>
<div xmlns="http://www.w3.org/1999/xhtml" id="xhr_form">
<form action="http://testserver:80/marionet/1/?__portlet_olGSLp__.action=process&amp;__portlet_olGSLp__.href=http%3A//localhost%3A3000/caterpillar/test_bench/ju
nit/xhr_hello" method="post" onsubmit="new Ajax.Updater('form_resp', '/caterpillar/test_bench/junit/xhr_hello', {asynchronous:true, evalScripts:true, parameters
:Form.serialize(this)}); return false;"><div><input name="commit" type="submit" value="send form POST" /></div></form><div id="form_resp"></div>
        """
        pass
        input = [etree.fromstring("""
            <input onclick="new Ajax.Updater('onclick_resp', '/caterpillar/test_bench/junit/xhr_hello', {asynchronous:true, evalScripts:true});" type="button" value="send onclick POST" />
            """)]
        session = MarionetSession.objects.create(
            location = 'http://example.com:8000/some-page',
            query = '',
            base = self.junit_base,
            )

        ctx_location = 'http://example.com:8000/some-page'
        session.set('location', ctx_location)
        session.set('baseURL', 'http://localhost:3000')

        _input = PageTransformer.input(None,
            input,
            [session]
            )[0] # take 1st _Element
        print _input.get('onclick')
        # XXX: use pyjamas?
        self.assertEqual(
            _input.get('onclick'),
            """
var portletRequest = new XMLPortletRequest("<portlet:namespace/>");
portletRequest.open("POST", "<portlet:resourceURL escapeXml='false' />");
portletReq.send(%s=%s&%s=%s);
            """ % (session.get('namespace')+'.href',
                'http%3A//localhost%3A3000/caterpillar/test_bench/junit/xhr_hello',
                session.get('namespace')+'.lifecycle',
                'serveResource')

            )        
        
