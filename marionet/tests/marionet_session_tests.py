# -*- coding: utf-8 -*-

# django imports
from django.contrib.auth.models import User
from django.template import RequestContext
from django.test import TestCase
from django.test.client import Client

# django-portlets imports
from portlets.models import PortletSession
import portlets.utils

from marionet import context_processors
from marionet.models import *
from marionet.tests.utils import RequestFactory

from BeautifulSoup import BeautifulSoup


class MarionetSessionTestCase(TestCase):

    def setUp(self):
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'


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

    def test_marionet_session_key(self):
        """ MarionetSession with key
        """
        _session_key = 'xTZsrE3fd5f'
        portlet = Marionet.objects.create(url='', session=False)
        (session,created) = MarionetSession.objects.get_or_create(portlet=portlet,django_key=_session_key)
        self.assert_(created)
        self.assertEqual(session.user, None)
        self.assertEqual(session.django_key, _session_key)
        self.assert_(session.id)

    def test_marionet_session_user(self):
        """ MarionetSession with key
        """
        user = User.objects.create_user(username="toejam", email="toejam@funkotron", password="jammin")
        portlet = Marionet.objects.create(url='', session=False)
        (session,created) = MarionetSession.objects.get_or_create(portlet=portlet,user=user)
        self.assert_(created)
        self.assertEqual(session.user, user)
        self.assertEqual(session.django_key, None)
        self.assert_(session.id)
        session_id = session.id

        (session,created) = MarionetSession.objects.get_or_create(portlet=portlet,user=user)
        self.assert_(not created)
        self.assertEqual(session.user, user)
        self.assertEqual(session.django_key, None)
        self.assertEqual(session.id, session_id)

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


