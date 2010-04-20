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

from urllib import quote, unquote

from marionet import log
from marionet.models import Marionet, PortletFilter
from marionet.models import WebClient
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
        self.assertEqual(portlet,_portlet)
        self.assertEqual(self.junit_url, _portlet.url)
        self.assertEqual('test portlet', _portlet.title)

    def test_render(self):
        """ Basic GET
        """
        url = self.junit_url
        portlet = Marionet(url=url,title='junit index')
        self.assert_(portlet)

        path = '/page/1'
        request = RequestFactory().get(path)
        ctx = RequestContext(request)
        ctx['path'] = request.path
        ctx['GET'] = request.GET

        out = portlet.render(ctx)
        self.assert_(out)
        self.assert_(portlet.context)
        self.assertEqual(path,portlet.context['path'])
        self.assertEqual(url,portlet.url)

    def test_portlet_url(self):
        """ Portlet URL
        """
        url = self.junit_url
        portlet = Marionet.objects.create(url=url,title='junit index')
        self.assert_(portlet)

        # target url
        href = url + '/target1'

        portlet_url_query = '%s_href=%s' % (portlet.namespace(), 
            quote(href.encode('utf8'))
            )

        path = '/page/1' + '?' + portlet_url_query
        request = RequestFactory().get(path)
        ctx = RequestContext(request)
        ctx['path'] = request.path
        ctx['GET'] = request.GET

        out = portlet.render(ctx)
        self.assert_(out)
        self.assert_(portlet.context)
        self.assertEqual('/page/1',portlet.context['path'])
        self.assertEqual(href,portlet.url)

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

