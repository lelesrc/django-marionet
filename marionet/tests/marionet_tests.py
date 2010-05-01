# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.template import RequestContext
from django.test import TestCase
from django.test.client import Client

# django-portlets imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot
from portlets.models import PortletSession
import portlets.utils

from marionet import log
from marionet import context_processors
from marionet.models import *
from marionet.tests.utils import RequestFactory
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

from urlparse import urlparse, urlunparse, urlunsplit, urljoin
from urllib import quote, unquote
from BeautifulSoup import BeautifulSoup


class MarionetTestCase(TestCase):
    """ XXX: if the url is given in POST parameters, create a PortletSession
    that will persist between requests.
    
    If the session is initialized without a Portlet (=> or Marionet) instance,
    a temporary one is created but not stored to the database.
    
    It is also possible to display a portlet without a session. This affects the
    portlet namespace and behavious, however. In Liferay this is called portlet
    "instanciablity".
    
    * TEST TEST TEST
    
    """

    def setUp(self):
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'


    def test_create(self):
        """ Database object creation
        """
        portlet = Marionet(
            url = self.junit_url,
            title = 'test portlet'
            )
        self.assert_(portlet)
        self.assert_(portlet.session)
        session = portlet.session
        del(portlet)

        # create portlet for this session
        portlet = Marionet.objects.create(session=session)
        self.assert_(portlet)
        self.assert_(portlet.session)
        self.assertEqual(portlet.session.id,session.id)
        self.assertEqual(portlet.url, self.junit_url)
        self.assertEqual(portlet.title, 'test portlet')
        self.assertEqual(portlet.session.get('baseURL'), self.junit_base)
        del(portlet)

        # create a new session
        portlet = Marionet.objects.create(
            url = self.junit_url,
            title = 'test portlet'
            )
        self.assert_(portlet)
        self.assert_(portlet.session)
        self.assertNotEqual(portlet.session.id,session.id) # ! different session
        self.assertEqual(portlet.url, self.junit_url)
        self.assertEqual(portlet.title, 'test portlet')
        self.assertEqual(portlet.session.get('baseURL'), self.junit_base)
        session_id = portlet.session.id
        portlet_id = portlet.id
        portlet.session.set('title', 'foobar')
        del(portlet)

        # check session
        portlet = Marionet.objects.get(id=portlet_id)
        self.assert_(portlet)

    def test_render_context_processor(self):
        """ Context preprocessor
        """
        path = '/page/1'
        request = RequestFactory().get(path)
        context = RequestContext(request)
        # render to call context preprocessor
        portlet = Marionet.objects.create(url=self.junit_url)
        portlet.render(context)

        location = context.get('location')
        self.assert_(location)
        self.assertEqual(location.scheme, 'http')
        self.assertEqual(location.netloc, 'testserver:80')
        self.assertEqual(location.path, path)

    def test_render(self):
        """ Basic GET
        """
        url = self.junit_url + '/index'
        portlet = Marionet.objects.create(url=url,title='junit index')
        self.assert_(portlet)
        self.assertEqual(portlet.id,1)
        session_name = portlet.session.name
        self.assert_(portlet.session)

        path = '/page/1'
        request = RequestFactory().get(path)
        context = RequestContext(request)

        out = portlet.render(context)

        self.assertEqual(portlet.url, url)
        self.assertEqual(portlet.title, 'junit index')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        #print soup
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
        self.assert_(portlet_div)

    def __test_target1(self,portlet,href):
        query = {
            '%s_href' % (portlet.session.get('namespace')): href
        }
        path = '/page/1'
        request = RequestFactory().get(path, query)
        context = RequestContext(request, [context_processors.render_ctx])

        out = portlet.render(context)
        self.assert_(out)
        #self.assert_(portlet.context)
        self.assertEqual(context.get('location').path, path)
        self.assertEqual(portlet.url,self.junit_base+'/caterpillar/test_bench/junit/target1')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
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
        portlet.session.set('baseURL', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)

        portlet = Marionet.objects.create(
            url=self.junit_url+'/', title='junit index')
        portlet.session.set('baseURL', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)

    def test_http_post(self):
        """
        url = self.junit_url+'/http_post'
        portlet = Marionet.objects.create(url=url)
        
        # POST to the same url
        href = url
        portlet_url_query = '%s_href=%s' % (portlet.session.get('namespace')), 
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
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
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

        context = RequestContext(request, [context_processors.render_ctx])
        # render portlet with the context
        portlet.render(context)
        render_url = portlet.render_url(href=None)
        self.assertEqual(render_url(), 'http://testserver:80/page/1')

    def test_portlet_url__get1(self):
        """ render url, single portlet
        """
        path = '/page/1'
        request = RequestFactory().get(path)
        context = RequestContext(request, [context_processors.render_ctx])
        portlet_url = self.junit_url
        href = portlet_url + '/target1'
        portlet = Marionet.objects.create(url=portlet_url)

        # give portlet the context
        portlet.render(context)
        # ..now we have the render url
        render_url = portlet.render_url(href)

        # render
        _url = render_url()
        #print _url
        request = RequestFactory().get(_url)
        context = RequestContext(request, [context_processors.render_ctx])

        qs = request.META['QUERY_STRING']
        #print qs
        self.assert_(
            re.match(
                portlet.session.get('namespace'),
                qs
                ),
            '%s has no portlet namespace' % (qs)
            )

        out = portlet.render(context)
        self.assertEqual(portlet.url, href)

    def test_preferences(self):
        portlet = Marionet.objects.create(url = self.junit_url)
        pref = PortletPreferences.objects.create(portlet=portlet)
        self.assert_(pref)
        elem = pref.elem()
        self.assertEqual(elem.__class__, lxml.etree._Element)
        self.assertEqual(elem.get('portlet_id'),
            str(portlet.id))
        self.assertEqual(elem.get('instance_id'),
            '1_INSTANCE_1')
        self.assert_(pref.tag())
        #print pref.portlet

    def test_marionet_session1(self):
        """ PortletSession callback
        """
        session = PortletSession.objects.create(
            url = self.junit_url,
            session_callback=Marionet.session_callback)

        self.assert_(session)
        self.assertEqual(session.get('url'), self.junit_url)
        self.assertEqual(session.get('namespace'), '__portlet_%s__' % session.name)
        self.assertEqual(session.get('baseURL'), self.junit_base)

        portlet = Marionet.objects.create(url = self.junit_url)
        self.assert_(portlet)
        self.assert_(portlet.session)
        self.assertEqual(portlet.session.get('url'), self.junit_url)
        self.assertEqual(portlet.session.get('namespace'), '__portlet_%s__' % portlet.session.name)
        self.assertEqual(portlet.session.get('baseURL'), self.junit_base)

    def test_view(self):
        c = Client()
        #response = c.post('/login/', {'username': 'john', 'password': 'smith'})
        #print response.status_code

        response = c.get('/test_bench/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        #print soup.html

    def test_xhr_marionet(self):
        """ XHR
        """
        c = Client()
        response = c.post('/test_bench/xhr',
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        self.assertEqual(len(portlets), 1)
        portlet_div = portlets[0]
        self.assert_(portlet_div)
        self.assertEqual(portlet_div.find('div').text, 'Hello World!')

    def test_xhr_marionet_fail(self):
        """ XHR FAIL
        """
        c = Client()
        response = c.post('/test_bench/xhr',
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        self.assertEqual(len(portlets), 1)
        portlet_div = portlets[0]
        self.assert_(portlet_div)
        self.assertEqual(portlet_div.find('div').text, '404 Not Found')

    def test_xhr_client_fail(self):
        """ django XHR Client FAIL
        """
        c = Client()
        response = c.get('/test_bench/xhr')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, 'FAIL')


