# -*- coding: utf-8 -*-
#

# django imports
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth.models import User
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

from marionet import context_processors
from marionet.models import *
from marionet.tests.utils import RequestFactory

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
            title = 'test portlet',
            session=True
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
        self.assertEqual(portlet.session.get('title'), 'test portlet')
        self.assertEqual(portlet.session.get('baseURL'), self.junit_base)
        del(portlet)

        # create a new session
        portlet = Marionet.objects.create(
            url = self.junit_url,
            title = 'test portlet',
            session=True
            )
        self.assert_(portlet)
        self.assert_(portlet.session)
        # XXX: session is volative if created with session=True!!!
        #self.assertNotEqual(portlet.session.id,session.id) # ! different session
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
        # XXX

    def test_render(self):
        """ Basic GET
        """
        url = self.junit_url + '/index'
        portlet = Marionet.objects.create(url=url,title='junit index', session=True)
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
        portlet_div = soup.find('div', {'class': '%s_body' % portlet.session.get('namespace')})
        self.assert_(portlet_div)

    def test_render_filter_href(self):
        portlet = Marionet.objects.create(session=True)
        self.assert_(portlet)
        url = self.junit_base+'/caterpillar/test_bench/'
        query = {
            '%s.href' % (portlet.session.get('namespace')): url
        }
        path = '/page/1'
        request = RequestFactory().get(path,query)
        context = RequestContext(request)

        out = portlet.render(context)

        self.assertEqual(portlet.url, url)
        self.assertEqual(portlet.title, 'Rails-portlet testbench')

    def __test_target1(self,portlet,href):
        # make a query string
        query = {
            '%s.href' % (portlet.session.get('namespace')): href
        }
        # context path
        path = '/page/1'
        request = RequestFactory().get(path, query)
        context = RequestContext(request, [context_processors.render_ctx])

        out = portlet.render(context)
        self.assert_(out)
        # context location should match
        location = portlet.session.get('location')
        self.assert_(location)
        loc = urlparse(location)
        self.assertEqual(loc.path, path)
        self.assertEqual(portlet.url,self.junit_base+'/caterpillar/test_bench/junit/target1')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find('div', {'class': '%s_body' % portlet.session.get('namespace')})
        self.assert_(portlet_div)
        link = portlet_div.find('a')
        self.assert_(link)
        #print link
        self.assertEqual(
            link.get('href'),
            'http://testserver:80/page/1?'+str(portlet.session.get('namespace'))+'.href=http%3A//localhost%3A3000/caterpillar/test_bench/junit/target2'
            )

    def test_portlet_url__absolute(self):
        """ Portlet URL with absolute url
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index', session=True)
        href = self.junit_url + '/target1'
        self.__test_target1(portlet,href)

    def test_portlet_url__absolute_path(self):
        """ Portlet URL with absolute path
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index', session=True)
        href = '/caterpillar/test_bench/junit/target1'
        self.__test_target1(portlet,href)

    def test_portlet_url__relative_path(self):
        """ Portlet URL with relative path
        """
        portlet = Marionet.objects.create(
            url=self.junit_url, title='junit index', session=True)
        portlet.session.set('baseURL', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)

        portlet = Marionet.objects.create(
            url=self.junit_url+'/', title='junit index', session=True)
        portlet.session.set('baseURL', self.junit_url) 
        href = 'target1'
        self.__test_target1(portlet,href)

    def test_http_post(self):
        url = self.junit_url+'/http_post'
        portlet = Marionet.objects.create(url=url, session=True)

        # POST to the same url
        href = url
        ns = portlet.session.get('namespace')
        query = QueryDict('')
        query._mutable = True
        query.__setitem__(ns+'.href', quote(href.encode('utf8')))
        query.__setitem__(ns+'.action', 'process') # processAction

        path = '/page/1' + '?' + query.urlencode()
        # POST params
        params = {'msg': 'test message'}
        request = RequestFactory().post(path, params)
        ctx = RequestContext(request)
        out = portlet.render(ctx) # XXX
        self.assert_(out)
        self.assertEqual(portlet.url, url)
        self.assert_(portlet.session)

        location = portlet.session.get('location')
        self.assertEqual(location, 'http://testserver:80/page/1')
        # portlet query string
        qs = portlet.session.get('qs')
        self.assertEqual(qs, 'msg=test+message')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'div')
        self.assertEqual(soup.find('head'), None)
        # namespace is correct
        portlet_div = soup.find('div', {'class': '%s_body' % ns})
        self.assert_(portlet_div)
        msg = portlet_div.find(id='post_msg')
        self.assertEqual(msg.text, params['msg'])

    def test_xhr_post(self):
        """ XHR POST
        """
        portlet = Marionet.objects.create(session=True)
        href = self.junit_url+'/xhr_post'
        ns = portlet.session.get('namespace')
        query = QueryDict('')
        query._mutable = True
        query.__setitem__(ns+'.href', quote(href.encode('utf8')))
        query.__setitem__(ns+'.action', 'process') # processAction
        query.__setitem__(ns+'.xhr', True) # set XHR

        path = '/page/1' + '?' + query.urlencode()
        # POST params
        params = {'msg': 'test message'}
        request = RequestFactory().post(path, params)
        context = RequestContext(request, [context_processors.render_ctx])
        #self.assertEqual(context['xhr?'], False)

        out = portlet.render(context)
        self.assert_(out)

        # test side effects
        self.assertEqual(portlet.url, href)
        self.assert_(portlet.session)
        self.assertEqual(portlet.session.get('xhr'),'1')
        location = portlet.session.get('location')
        self.assertEqual(location, 'http://testserver:80/page/1')
        # portlet query string
        qs = portlet.session.get('qs')
        self.assertEqual(qs, 'msg=test+message')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual(soup.find().name, 'hash')
        msg = soup.find(name='msg')
        self.assert_(msg)
        self.assertEqual(msg.text, params['msg'])

    def test_xhr_marionet1(self):
        """ Django receives XHR, portlet GET
        """
        user = User.objects.create_user(username="toejam", email="toejam@funkotron", password="jammin")
        c = Client()
        login = c.login(username='toejam', password='jammin')
        portlet = Marionet.objects.create(url=self.junit_url+'/check_xhr', session=True)
        response = c.post('/marionet/%s/' % portlet.id,
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        self.assertEqual(len(portlets), 1)
        portlet_div = portlets[0]
        self.assert_(portlet_div)
        self.assertEqual(portlet_div.find('div').text, 'false')

    def test_xhr_marionet2(self):
        """ Django receives GET, portlet XHR
        """
        user = User.objects.create_user(username="earl", email="earl@funkotron", password="burb")
        c = Client()
        login = c.login(username='earl', password='burb')
        portlet = Marionet.objects.create(url=self.junit_url+'/check_xhr', session=True)
        portlet.session.set('xhr','1')
        #portlet.session.save()
        response = c.get('/marionet/%s/' % portlet.id)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        self.assertEqual(len(portlets), 1)
        portlet_div = portlets[0]
        self.assert_(portlet_div)
        self.assertEqual(portlet_div.text, 'true')

    '''
    def test_not_found(self):
        """ 
        """
        self.assertEqual(portlet_div.find('div').text, '404 Not Found')
    '''

