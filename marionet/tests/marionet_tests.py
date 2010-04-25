# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.template import RequestContext
from django.test import TestCase

# reviews imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot
import portlets.utils

from urlparse import urlparse, urlunparse, urlunsplit, urljoin
from urllib import quote, unquote
from BeautifulSoup import BeautifulSoup

from marionet import log
from marionet.models import *
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

#import inspect
#import libxml2
#from copy import copy


class MarionetTestCase(TestCase):

    def setUp(self):
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'
        #self.session_secret='xxx'

    '''

    def test_create(self):
        """ Database object creation
        """
        portlet = Marionet.objects.create(
            url = self.junit_url,
            title = 'test portlet'
            )
        self.assert_(portlet)
        _portlet = Marionet.objects.get(id=portlet.id)
        self.assert_(_portlet)
        self.assertEqual(_portlet,portlet)
        self.assertEqual(_portlet.url, self.junit_url)
        self.assertEqual(_portlet.title, 'test portlet')
        self.assertEqual(_portlet.session.get('base'), self.junit_base)

    def test_render(self):
        """ Basic GET
        """
        url = self.junit_url + '/index'
        portlet = Marionet.objects.create(url=url,title='junit index')
        self.assert_(portlet)
        self.assertEqual(portlet.id,1)
        self.assertEqual(portlet.namespace(),'__portlet_1__')

        path = '/page/1'
        request = RequestFactory().get(path)
        out = portlet.render(request)
        self.assert_(out)
        self.assert_(portlet.context)
        self.assertNotEqual(portlet.session, None)
        self.assertEqual(portlet.context.get('location').path, path)
        self.assertEqual(portlet.url, url)
        self.assertEqual(portlet.title, 'junit index')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.namespace())
        self.assert_(portlet_div)

    def __test_target1(self,portlet,href):
        query = {
            '%s_href' % (portlet.namespace()): href
        }
        path = '/page/1'
        request = RequestFactory().get(path, query)
        """
        ctx = RequestContext(request)
        ctx['path'] = request.path
        ctx['GET'] = request.GET
        """
        out = portlet.render(request)
        self.assert_(out)
        self.assert_(portlet.context)
        self.assertEqual(portlet.context.get('location').path, path)
        self.assertEqual(portlet.url, 
            self.junit_base+'/caterpillar/test_bench/junit/target1')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.namespace())
        self.assert_(portlet_div)
        link = portlet_div.find('a')
        self.assert_(link)

    def test_portlet_url__absolute(self):
        """ Portlet URL with absolute url
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index')
        href = self.junit_url + '/target1'
        self.__test_target1(portlet,href)

    def test_portlet_url__absolute_path(self):
        """ Portlet URL with absolute path
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index')
        href = '/caterpillar/test_bench/junit/target1'
        self.__test_target1(portlet,href)

    def test_portlet_url__relative_path(self):
        """ Portlet URL with relative path
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index')
        portlet.session.set('base', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)

        portlet = Marionet.objects.create(
            url=self.junit_url+'/', title='junit index')
        portlet.session.set('base', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)


    def test_http_post(self):
        """
        url = self.junit_url+'/http_post'
        portlet = Marionet.objects.create(url=url)
        
        # POST to the same url
        href = url
        portlet_url_query = '%s_href=%s' % (portlet.namespace(), 
            quote(href.encode('utf8'))
            )
        path = '/page/1' + '?' + portlet_url_query
        params = {'msg': 'test message'}
        request = RequestFactory().post(path, params)

        ctx = RequestContext(request)
        ctx['path'] = request.path
        ctx['GET'] = request.GET
        ctx['POST'] = request.POST

        out = portlet.render(ctx)
        self.assert_(out)
        self.assert_(portlet.context)
        self.assertEqual(portlet.context['path'],'/page/1')
        self.assertEqual(portlet.url, url)

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.namespace())
        self.assert_(portlet_div)
        print portlet_div
        msg = portlet_div.find(id='post_msg')
        self.assertEqual(msg.text, params['msg'])
        print msg #.text
#        link = portlet_div.find('a')
#        self.assert_(link)
        """

    def __test_render_url(self):
        pass

    def test_render_url__no_href(self):
        path = '/page/1'
        request = RequestFactory().get(path)
        portlet_url = self.junit_url

        portlet = Marionet.objects.create(url=portlet_url)
        # give portlet the context
        portlet.render(request)
        render_url = portlet.render_url(None)
        self.assertEqual(render_url(), 'http://testserver:80/page/1')

    def test_portlet_url__get1(self):
        """ render url, single portlet
        """
        path = '/page/1'
        request = RequestFactory().get(path)
        portlet_url = self.junit_url
        href = portlet_url + '/target1'

        portlet = Marionet.objects.create(url=portlet_url)
        # give portlet the context
        portlet.render(request)
        # ..now we have the render url
        render_url = portlet.render_url(href)

        # render
        _url = render_url()
        request = RequestFactory().get(_url)

        qs = request.META['QUERY_STRING']
        self.assert_(
            re.match(
                portlet.namespace(),
                qs
                ),
            '%s has no portlet namespace' % (qs)
            )

        out = portlet.render(request)
        self.assertEqual(portlet.url, href)

    #'''

    def test_preferences(self):
        portlet = Marionet.objects.create(url = self.junit_url)
        pref = PortletPreferences(portlet)
        self.assert_(pref)
        elem = pref.elem()
        self.assertEqual(elem.__class__, lxml.etree._Element)
        self.assertEqual(elem.get('portletid'), str(portlet.id))
        self.assert_(pref.tag())


    ''' secret is not used yet
    def test_secret(self):
        """
        """
        mn_portlet = Marionet(session_secret=self.session_secret)
        self.assert_(mn_portlet)
        self.assertEqual(self.session_secret,mn_portlet.session_secret)
        out = mn_portlet.render() # calls filter + changes state!
        self.assertNotEqual(None,out)
    '''

