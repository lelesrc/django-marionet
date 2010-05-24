# -*- coding: utf-8 -*-
#

from django.test import TestCase

from marionet.models import Marionet, WebClient, PageProcessor, MarionetSession
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


class PageProcessorTestCase(TestCase):
    def setUp(self):
        self.junit_base = 'http://localhost:3000'
        self.junit_url = self.junit_base + '/caterpillar/test_bench/junit'


    def test_transform(self):
        ''' Basic body transformation
        '''
        url = self.junit_url+'/xslt_simple'
        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)
        self.assert_(tree)
        # trigger side effects!
        tree = PageProcessor.append_metadata(tree,portlet.session)
        #
        out = PageProcessor.transform(tree,portlet.session)
        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual('div', soup.find().name)
        self.assertEqual(None, soup.find('head'))
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
        self.assert_(portlet_div)

    def test_parse_tree(self):
        ''' HTML tree parse
        '''
        url = self.junit_url+'/xslt_simple'
        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)
        self.assertEqual(tree.__class__, etree._ElementTree)
        # test meta data
        # trigger side effects!
        tree = PageProcessor.append_metadata(tree,portlet.session)
        #
        portlet_tag = tree.find('//head/portlet-session')
        self.assertEqual(portlet_tag.__class__, etree._Element)
        self.assertEqual(portlet_tag.get('namespace'), portlet.session.get('namespace'))
        self.assertEqual(portlet_tag.get('baseURL'), self.junit_base)

    def test_bench_tree(self):
        ''' Portlet test bench index
        '''
        url = self.junit_base + '/caterpillar/test_bench'
        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)
        self.assertEqual(tree.__class__, etree._ElementTree)
        # test meta data
        # trigger side effects!
        tree = PageProcessor.append_metadata(tree,portlet.session)
        #
        portlet_tag = tree.find('//head/portlet-session')
        self.assertEqual(portlet_tag.__class__, etree._Element)
        self.assertEqual(portlet_tag.get('namespace'), portlet.session.get('namespace'))
        self.assertEqual(portlet_tag.get('baseURL'), self.junit_base)

    def test_parse_empty_tree(self):
        ''' Empty tree parse
        '''
        url = self.junit_url+'/empty'
        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        tree = PageProcessor.parse_tree(response)
        self.assertEqual(etree._ElementTree, tree.__class__)
        # test meta data
        # trigger side effects!
        tree = PageProcessor.append_metadata(tree,portlet.session)
        #
        portlet_tag = tree.find('head/portlet-session')
        self.assertEqual(portlet_tag.__class__, etree._Element)
        self.assertEqual(portlet_tag.get('namespace'), portlet.session.get('namespace'))
        self.assertEqual(portlet_tag.get('baseURL'), self.junit_base)

    def test_process(self):
        ''' Portlet processing chain
        '''
        url = self.junit_url+'/xslt_simple'
        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual('div', soup.find().name)
        self.assertEqual(None, soup.find('head'))
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
        self.assert_(portlet_div)

    def test_append_metadata(self):
        tree = etree.fromstring('''
<html>
  <head>
    <title>
      awesome title
    </title>
    <base href="http://example.com/resources" />
    <meta http-equiv="content-type" content="text/html; charset=UTF-8"></meta>
  </head>
</html>
            ''').getroottree()
        session = MarionetSession()
        tree = PageProcessor.append_metadata(tree,session)

        self.assertEqual(session.get('baseURL'), 'http://example.com/resources')
        self.assertEqual(session.get('title'), 'awesome title')

        head_session = tree.find('//head/portlet-session')
        self.assertEqual(head_session.get('baseURL'), 'http://example.com/resources')
        self.assertEqual(head_session.get('title'), 'awesome title')
        self.assertEqual(head_session.get('namespace'), session.get('namespace'))


    def test_title(self):
        ''' Portlet title
        '''
        portlet = Marionet(session=True)
        self.assertEqual(portlet.title, '')
        html = '''
<html>
  <head>
    <title>
      funkadelic title
    </title>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8"></meta>
  </head>
</html>
            '''
        response = ResponseMock(body=html)
        self.assert_(response)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)
        self.assertEqual(portlet.session.get('title'),'funkadelic title')

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual('div', soup.find().name)
        self.assertEqual(None, soup.find('head'))

    def test_title_bad(self):
        ''' Empty portlet title
        '''
        portlet = Marionet(session=True)
        html = '''
<html>
  <head>
  </head>
</html>
            '''
        response = ResponseMock(body=html)
        self.assert_(response)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)
        self.assertEqual(None,portlet.session.get('title'))

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual('div', soup.find().name)
        self.assertEqual(None, soup.find('head'))

    def test_images(self):
        ''' Image url rewrite
        '''
        url = self.junit_url+'/basic_tags'
        portlet = Marionet(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)
        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        #print soup
        # absolute url
        img_url = 'http://localhost:3000/images/portlet_test_bench/rails.png'
        self.assertEqual(
            soup.find(id='image_absolute_url').findNext('img')['src'],
            img_url
            )
        # relative url
        self.assertEqual(
            soup.find(id='image_absolute_path').findNext('img')['src'],
            img_url
            )
        # explicit base url
        self.assertEqual(
            soup.find(id='image_relative_path').findNext('img')['src'],
            img_url
            )
    '''
    def test_images_relative_path_navigation(self):
        portlet = Marionet(url='http://example.com', session=True)
        self.fail()
    '''

    def test_css(self):
        ''' CSS rewrite
        '''
        url = self.junit_url+'/css'
        portlet = Marionet(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)
        #print out
        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # absolute url
        css_url = 'http://localhost:3000/stylesheets/portlet_test_bench/main.css'
        # search for inline @import url
        url = re.search('@import "([^"]*)', soup.find(id='absolute_style_url').text).group(1)
        self.assert_(url)
        self.assertEqual(
            css_url,
            url
            )
        # absolute path
        url = re.search('@import "([^"]*)', soup.find(id='absolute_style_path').text).group(1)
        self.assert_(url)
        self.assert_(
            re.match(
                r'^%s?(.*)' % (css_url),
                url
                ),
            '%s ~= %s' % (url,css_url)
            )
        # style_in_body
        self.assert_(soup.find(id='absolute_style_path').text)
        # style in attribute
        self.assert_(soup.find(id='style_attribute')['style'])

    def test_links(self):
        ''' Link rewrite
        '''
        url = self.junit_url+'/basic_tags'
        portlet = Marionet.objects.create(url=url, session=True)
        # get test data
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)

        portlet.session.set('location', 'http://example.com:8000/some-page')
        out = PageProcessor.process(response,portlet.session)

        soup = BeautifulSoup(out)
        link = soup.find(id='anchor_absolute_url').find('a')
        self.assertEqual(
            'http://example.com:8000/some-page?'+str(portlet.session.get('namespace'))+'.href=http%3A//localhost%3A3000/caterpillar/test_bench',
            link.get('href') 
            )

    def test_link(self):
        # XSLT returns this form
        location = 'http://example.com:8000/some-page'
        query = ''
        anchor = [etree.fromstring('<a href="/caterpillar/test_bench">Link text</a>')]
        namespace = '__portlet__'
        link = PageProcessor.link(None,
            anchor,
            location,
            query,
            namespace,
            self.junit_base
            )[0] # take 1st _Element
        self.assertEqual(
            link.get('href'),
            'http://example.com:8000/some-page?__portlet__.href=http%3A//localhost%3A3000/caterpillar/test_bench')
        #print etree.tostring(link)

    def test_form(self):
        # XSLT returns this form
        location = 'http://example.com:8000/some-page'
        query = ''
        form = [etree.fromstring('''
            <form action="/caterpillar/test_bench/http_methods/post" method="post">
              <p>
                <span>Input text:</span>
                <input id="msg" name="msg" size="42" type="text" value="Python was conceived in the late 1980s and its implementation was started in December 1989 by Guido van Rossum" />
              </p>
            </form>
            ''')]

        namespace = '__portlet__'
        _form = PageProcessor.form(None,
            form,
            location,
            query,
            namespace,
            self.junit_base
            )[0] # take 1st _Element
        self.assertEqual(
            _form.get('action'),
            'http://example.com:8000/some-page?__portlet__.href=http%3A//localhost%3A3000/caterpillar/test_bench/http_methods/post&__portlet__.action=process')

    def __test_doctype(self,type):
        ''' Same test for different DOCTYPEs
        '''
        url = self.junit_url+'/doctype_'+type

        portlet = Marionet.objects.create(url=url, session=True)
        client = WebClient()
        self.assert_(client)
        response = client.get(url)
        self.assertEqual(200, response.status)
        out = PageProcessor.process(response,portlet.session)
        self.assert_(out)

        soup = BeautifulSoup(str(out))
        self.assert_(soup)
        # only body remains
        self.assertEqual('div', soup.find().name)
        self.assertEqual(None, soup.find('head'))
        # namespace is correct
        portlet_div = soup.find(id='%s_body' % portlet.session.get('namespace'))
        self.assert_(portlet_div)

        # base + title + content are correct
        self.assertEqual('http://127.0.0.10:3000/',portlet.session.get('baseURL'))
        self.assertEqual('Portlet title',portlet.session.get('title'))
        self.assertEqual('Portlet content',portlet_div.text)

    def test_undefined_doctype(self):
        ''' Undefined HTML doctype
        '''
        self.__test_doctype('undefined')

    def test_html4_strict(self):
        ''' HTML 4.01 Strict
        '''
        self.__test_doctype('html4_strict')

    def test_xhtml10_strict(self):
        ''' XHTML 1.0 Strict
        '''
        self.__test_doctype('xhtml10_strict')

    def test_xhtml10_trans(self):
        ''' XHTML 1.0 Transitional
        '''
        self.__test_doctype('xhtml10_transitional')

    def test_xhtml11(self):
        ''' XHTML 1.1
        '''
        self.__test_doctype('xhtml11')

    def test_html5(self):
        ''' HTML 5
        '''
        self.__test_doctype('html5')

    """ xslt does not handle this

    def test_html5_minified(self):
        ''' Minified HTML 5
        '''
        self.__test_doctype('html5_minified')

    """
