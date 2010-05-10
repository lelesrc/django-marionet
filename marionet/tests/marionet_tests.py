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
        print portlet.session
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

    def test_render_context_processor(self):
        """ Context preprocessor
        """
        path = '/page/1'
        request = RequestFactory().get(path)
        context = RequestContext(request)
        # render to call context preprocessor
        portlet = Marionet.objects.create(url=self.junit_url, session=True)
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
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
        self.assert_(portlet_div)

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
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
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
        portlet_div = soup.find(id='%s_body' % ns)
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

    def __test_render_url(self):
        pass

    def test_render_url__no_href(self):
        path = '/page/1'
        request = RequestFactory().get(path)
        portlet_url = self.junit_url
        portlet = Marionet.objects.create(url=portlet_url, session=True)

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
        portlet = Marionet.objects.create(url=portlet_url, session=True)

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
        """ PortletSession namespace and baseURL
        """
        """
        portlet = Marionet.objects.create(
            url = self.junit_url,
            session_callback=Marionet.session_callback)

        self.assert_(session)
        self.assertEqual(session.get('url'), self.junit_url)
        self.assertEqual(session.get('namespace'), '__portlet_%s__' % session.name)
        self.assertEqual(session.get('baseURL'), self.junit_base)
        """
        portlet = Marionet.objects.create(url = self.junit_url, session=True)
        self.assert_(portlet)
        self.assert_(portlet.session)
        self.assertEqual(portlet.session.get('url'), self.junit_url)
        self.assertEqual(portlet.session.get('namespace'), '__portlet_%s__' % portlet.session.name)
        self.assertEqual(portlet.session.get('baseURL'), self.junit_base)

    def test_marionet_session2(self):
        """ Session location and query with GET
        """
        query = {
            'foo': 'bar'
        }
        path = '/page/1'
        request = RequestFactory().get(path, query)
        context = RequestContext(request, [context_processors.render_ctx])

        portlet = Marionet.objects.create(url = self.junit_url, session=True)
        location = portlet.session.get('location')
        self.assertEqual(location,None)

        out = portlet.render(context)

        location = portlet.session.get('location')
        self.assertEqual(location, 'http://testserver:80/page/1')
        query = portlet.session.get('query')
        self.assertEqual(query, 'foo=bar')

    def test_marionet_session3(self):
        """ MarionetSession with user.
            Creates a new session on first request, and retrieves it on the second request.
        """
        user = User.objects.create_user(
            username="lion",
            email="untamed_animal@savanna.ke",
            password="roar"
            )
        c = Client()
        login = c.login(username='lion', password='roar')
        self.failUnless(login, 'Could not log in')

        portlet = Marionet.objects.create(url=self.junit_url,session=False)
        # there should be no existing session
        self.assertEqual(portlet.session, None)
        self.assertRaises(MarionetSession.DoesNotExist,
            MarionetSession.objects.get, portlet=portlet, user=user)

        response = c.get('/marionet/%s/' % portlet.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].username, 'lion')
        # no more trace of volatile portlet session
        self.assertEqual(portlet.session, None)
        # but the session should exist in the database
        session = MarionetSession.objects.get(portlet=portlet, user=user)
        portlet_body_id = '%s_body' % session.get('namespace')
        self.assert_(session)
        self.assertEqual(session.user_id, user.id)
        # does the portlet output the correct namespace?
        soup = BeautifulSoup(response.content)
        portlet_div = soup.find(id=portlet_body_id)
        self.assert_(portlet_div)

        # request again to see that the view loads the correct session,
        # instead of creating a new one
        del(response)
        response = c.get('/marionet/%s/' % portlet.id)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        portlet_div = soup.find(id=portlet_body_id)
        self.assert_(portlet_div)

    def test_marionet_session4(self):
        """ MarionetSession with user
        """
        user = User.objects.create_user(username="lion", email="fred@savanna.ke", password="roar")
        portlet = Marionet.objects.create(url=self.junit_url,session=False)
        self.assertEqual(portlet.session, None)
        session = MarionetSession(user=user,portlet=portlet)
        self.assert_(session)
        self.assertEqual(session.user, user)
        self.assertEqual(session.portlet, portlet)
        self.assertEqual(portlet.session, None) # no side effects
        session.save()
        portlet.session = session
        portlet.save()
        del(session)
        id = portlet.id
        del(portlet)
        portlet = Marionet.objects.get(id=id)
        # session is not stored to the portlet
        self.assertEqual(portlet.session, None)

    def test_marionet_session5(self):
        """ MarionetSession without portlet
        """
        user = User.objects.create_user(username="lion", email="fred@savanna.ke", password="roar")
        session = MarionetSession(user=user)
        self.assert_(session)
        self.assertEqual(session.user, user)

    def test_marionet_session6(self):
        """ MarionetSession with extra attributes
        """
        user = User.objects.create_user(username="lion", email="fred@savanna.ke", password="roar")
        session = MarionetSession(user=user, url='http://example.com')
        self.assert_(session)
        self.assertEqual(session.user, user)
        self.assertEqual(session.get('url'), 'http://example.com')
        session.save()
        id = session.id
        del(session)
        session = MarionetSession.objects.get(id=id)
        self.assertEqual(session.get('url'), 'http://example.com')

    def test_marionet_session7(self):
        """ MarionetSession with key
        """
        _session_key = 'xTZsrE3fd5f'
        session = MarionetSession.objects.create(key=_session_key)
        self.assert_(session)
        self.assertEqual(session.user, None)
        self.assertEqual(session.key, _session_key)
        self.assert_(session.id)

    def __test_session_id(self,client):
        portlet = Marionet.objects.create(url=self.junit_url+'/session_cookie', session=True)
        response = client.get('/marionet/%s/' % portlet.id)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        session_id = portlets[0].find('hash').find('id').text

        # request again!
        response = client.get('/marionet/%s/' % portlet.id)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assert_(soup)
        portlets = soup.findAll('div', {'class': 'marionet_content'})
        _session_id = portlets[0].find('hash').find('id').text

        self.assertEqual(session_id, _session_id)

    def test_marionet_session8(self):
        """ MarionetSession and cookies for anonymous user
        """
        self.__test_session_id(Client())

    def test_marionet_session9(self):
        """ MarionetSession and cookies for registered user
        """
        user = User.objects.create_user(username="toejam", email="toejam@funkotron", password="jammin")
        c = Client()
        login = c.login(username='toejam', password='jammin')
        self.__test_session_id(c)

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
        print portlet_div
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
        print portlet_div
        self.assertEqual(portlet_div.text, 'true')

    '''
    def test_not_found(self):
        """ 
        """
        self.assertEqual(portlet_div.find('div').text, '404 Not Found')
    '''

