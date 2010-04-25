# -*- coding: utf-8 -*-
#
# In the works.

# django imports
from django import forms
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log, Config

import re
import httpclient
import traceback
from singletonmixin import Singleton
from lxml import etree
import lxml.html.soupparser
from StringIO import StringIO
from urlparse import urlparse, urlunparse, urlsplit, urlunsplit, urljoin, ParseResult
from cgi import parse_qs
from urllib import quote, unquote
from posixpath import normpath
from copy import copy


class PortletPreferences(models.Model):
    """ A portlet instance for the user, who has set specific preferences.
    """
    portletid        = models.IntegerField()

    def __init__(self, portlet, *args, **kwargs):
        self.portlet   = portlet
        self.portletid = portlet.id

    def elem(self):
        elem = etree.Element("portlet-preferences")
        elem.set('portletid', '%s' % (self.portletid))
        return elem

    def tag(self):
        return etree.tostring(self.elem())


class PortletURL():
    def __init__(self, location, query, *args, **kwargs):
        """ Not to be initialized manually. Use static functions.
        """
        self.location = location
        self.query = query

    def __call__(self):
        return self.__unicode__()

    def __unicode__(self):
        """ "tostring"
        """
        qs = "&".join(map(lambda (k,v): '%s=%s' % (
            k,quote(v.encode('utf8'))),
            self.query.items()))
        return urlunsplit((
            self.location.scheme,
            self.location.netloc,
            self.location.path,
            qs,
            ''
            ))

    @staticmethod
    def render_url(location, query={}, namespace=None, href=None, base=None, params={}, method='GET'):
        """ 
        """
        log.debug('portlet href: %s' % (href))
        if href is None:
            return PortletURL(location, query)

        if base is not None:
            # rewrite url
            href = PageProcessor.href(None,href,base)

        # append portlet parameters to query
        log.debug('context query: %s' % (query))
        query[namespace+'_href'] = href

        return PortletURL(location, query)

    @staticmethod
    def action_url(*args):
        ''' UNIMPLEMENTED '''
        pass

    @staticmethod
    def resource_url(*args):
        ''' UNIMPLEMENTED '''
        pass


class PortletFilter():

    @staticmethod
    def render_filter(view_func):
        """
        Filter for portlet render requests.

        If the context url contains a new href for this portlet
        instance, the portlet.url is updated.
        """
        def do_filter(portlet, request, context=None):
            log.debug(' * * * render filter activated')
            #log.debug(portlet.url)
            #log.debug(portlet.base)
            #log.debug(context['GET'])
            if not context:
                context = RequestContext(request)
            context['location'] = ParseResult(
                'http',
                '%s:%s' % (request.META['SERVER_NAME'], request.META['SERVER_PORT']),
                request.path,
                '',
                request.META['QUERY_STRING'],
                ''
                )
            context['query'] = parse_qs(context.get('location').query)
            context['GET'] = request.GET
            #log.debug(context['query'])

            href_key = '%s_href' % (portlet.namespace())
            #log.debug(href_key)
            if context['GET'].__contains__(href_key):
                href = context['GET'].__getitem__(href_key)
                log.debug('portlet href: %s' % (href))
                # rewrite url
                url = PageProcessor.href(None,href,portlet.session.get('base'))
                log.debug('new url: %s' % (url))
                # update portlet
                portlet.url = unquote(url)
            else:
                log.debug('no href key')
            return view_func(portlet,request,context)

        do_filter.__name__ = view_func.__name__
        do_filter.__dict__ = view_func.__dict__
        do_filter.__doc__  = view_func.__doc__

        return do_filter


class Marionet(Portlet):
    """ This is still a mess.
    """
    VERSION = '0.0.1'

    url        = models.TextField(u"url",        blank=True)
    req_method = models.TextField(u"req_method", blank=True)
    referer    = models.TextField(u"referer",    blank=True)

    # session values
    session = None
    base = None

    # session secret for security given at init, not stored to DB
    #session_secret = None
    
    def __init__(self, *args, **kwargs):
        #if 'session_secret' in kwargs:
        #    self.session_secret = kwargs['session_secret']
        #    del kwargs['session_secret']
        Portlet.__init__(self, *args, **kwargs)
        log.info("Marionet (v%s) '%s', id %s" % (self.VERSION,self.title,self.id))
        self.session = etree.Element("portlet")
        self.session.set('id', '%s' % (self.id))
        _url = urlparse(self.url)
        self.session.set('base',
            '%s://%s' % (_url.scheme, _url.netloc))
        #log.debug(etree.tostring(self.session))

    def __unicode__(self):
        return self.url

    def namespace(self):
        return '__portlet_%s__' % (self.id)

    @PortletFilter.render_filter
    def render(self, request, context):
        """ Render GET.

            This method has side effects; the self.title is set only
            after render() is called, but currently the portlet title
            is inserted to the page before rendering, thus the title
            is empty...
        """
        log.info(" * * * render * "+self.url)
        #log.debug('context: %s' % (context))
        #log.debug('context path: %s' % (context['path']))
        try:
            client = WebClient()
            # this is the response from the remote server
            response = client.get(self.url)
            # process the response in this portlet context with this sheet
            self.context = copy(context)
            (out,meta) = PageProcessor.process(response,self,sheet='body')
            log.info('title: '+self.title)
            log.info('Page length: %i bytes' % (len(out)))
            return out
        except:
            log.error(traceback.format_exc())
            return "ERROR"

    def render_url(self, href, params={}):
        """ Calls the function with portlet state parameters.
        """
        return PortletURL.render_url(
            location = self.context.get('location'),
            query = self.context.get('query'),
            href = href,
            params = params,
            namespace = self.namespace(),
            method = 'GET',
            base = self.base,
            )

    '''
    def action_url(self, href, params={}):
        return PortletURL.action_url(
            self.context,
            {
                'namespace': self.namespace(),
                'method': 'POST',
                'base': self.base,
                'href': href,
                'params': params
            })
    '''


    def form(self, **kwargs):
        """
        """
        return MarionetForm(instance=self, **kwargs)

class MarionetForm(forms.ModelForm):
    """Form for Marionet.
    """
    class Meta:
        model = Marionet

register_portlet(Marionet, "Marionet")


class WebClient():
    """ Modeled after OnlineClient in html2jsr286.
        Handles state maintenance, in that after each request
        cookies are updated.
    """

    def __init__(self,*args,**kwargs):
        """ Store cookies to the instance. """
        if 'cookies' in kwargs:
            self.cookies = kwargs['cookies']
        else:
            self.cookies = {}

        self.__config = httpclient.Configuration()
        self.__config.set_user_agent(
            '# Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100130 Gentoo Firefox/3.6')
        #config.set_trust_store("/path/to/verisign/ca.pem")

    def update_cookies(self,response):
        """ Update cookies from HTTP response header 'Set-Cookie'.

            Cookies are never implicitly removed from the headers.

            BEWARE: httpclient cannot handle cookies
            scattered over multiple lines, which is valid
            in HTTP headers.
        """
        server_cookies = response.getheader('Set-Cookie')
        if server_cookies:
            for cookie in map(lambda f: f.split('; '), server_cookies.split(', ')):
                name = cookie[0].split('=')[0]
                self.cookies[name] = cookie
            log.debug("Stored %i cookies: %s" % (len(self.cookies),self.cookies))

    def add_cookies(self,cookies):
        """ Add cookies from dict.
            Format: {'foo': ['foo=bar'], 'baz': ['baz=xyz']}
        """
        self.cookies.update(cookies)

    def cookie_headers(self):
        """ Parse cookies to HTTP header string. 
        """
        return '; '.join(map(lambda f: f[0], self.cookies.values()))

    def get(self,url,referer=None):
        """ Execute GET request.
            Returns httplib.HTTPResponse.
        """
        log.info('GET %s' % (url))
        method = httpclient.GetMethod(url)
        # add cookies
        method.add_request_header('Cookie',self.cookie_headers())
        #log.debug(method.getheaders())
        method.execute()
        response = method.get_response()
        #log.debug(response.getheaders())
        self.update_cookies(response) # updates state
        return response

    def post(self,url,params={}):
        """ Execute POST request.
            Returns httplib.HTTPResponse.
        """
        method = httpclient.PostMethod(url)
        # add parameters to request body
        body = '&'.join(map(lambda (k,v): k+"="+v, params.items()))
        method.set_body(body)
        # add cookies
        method.add_request_header('Cookie',self.cookie_headers())
        # httpclient forgets cookies with automatic redirect..
        method.set_follow_redirects(0)
        #log.debug(method.getheaders())
        method.execute()
        response = method.get_response()
        #log.debug(response.getheaders())
        # server redirect does not echo sent cookies, but may set new ones
        self.update_cookies(response) # updates state
        # follow redirect..
        if response.status == 302 or response.status == 301:
            return self.get(response.getheader('Location'))
        else:
            return response


class PageProcessor(Singleton):
    """ Functions for page transformation and metadata parsing.
    """

    def __init__(self,*args,**kwargs):
        """ Define available xslt sheets. 
        """
        self.sheets = {'body': self.__body_xslt()}
        ns = etree.FunctionNamespace('http://github.com/youleaf/django-marionet')
        ns.prefix = "marionet"
        ns['link'] = PageProcessor.link
        ns['image'] = PageProcessor.image
        ns['href'] = PageProcessor.href


    def __body_xslt(self):
        """ Define body transformation stylesheet.
        """
        log.debug('define xslt - this message should only appear at startup')
        return etree.XML('''\
<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:marionet="http://github.com/youleaf/django-marionet"
     >

    <xsl:namespace-alias stylesheet-prefix="xmlns:marionet" 
          result-prefix=""/>

    <xsl:output method="html" omit-xml-declaration="yes"/>

    <!--
    <xsl:param name="foo" required="yes" />
    -->

    <xsl:variable
        name="namespace"
        select="//*[local-name()='head']/portlet/@namespace" />

    <xsl:variable
        name="base"
        select="//*[local-name()='head']/portlet/@base" />


    <!-- Fetch some info from head, and all of body -->
    <xsl:template match="*[local-name()='html']">
        <div id="{$namespace}_body">
            <xsl:apply-templates select="*[local-name()='head']/link"/>
            <xsl:apply-templates select="*[local-name()='head']/style"/>
            <xsl:apply-templates select="*[local-name()='body']"/>
        </div>
    </xsl:template>

    <xsl:template match="body">
        <xsl:apply-templates select="node()"/>
    </xsl:template>

    <!-- Rewrite links -->
    <xsl:template match="a">
        <xsl:copy-of select="marionet:link(.,string($namespace),string($base))"/>
    </xsl:template>

    <!-- Rewrite image references -->
    <xsl:template match="img">
      <xsl:copy-of select="marionet:image(.,string($base))"/>
      <div id="{$foo}" />
    </xsl:template>

    <!-- Convert link tags in head to style tags -->
    <xsl:template match="/html/head/link">
        <style type="text/css" id="{@id}">
        @import "<xsl:value-of select="marionet:href(string(@href),string($base))"/>";
        </style>
    </xsl:template>

    <!-- Copy through everything that hasn't been modified by the processor -->
    <xsl:template match="text()|@*|*">
        <xsl:copy>
          <xsl:apply-templates select="*|@*|text()"/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>''')


    @staticmethod
    def parse_tree(response):
        """ Parses the response HTML.
            In case the input is badly formatted HTML, the soupparser is used.
        """
        html = response.read()
        """
        log.debug(' # input HTML')
        log.debug(html)
        log.debug(' # # #')
        """
        try:
            root = etree.fromstring(html).getroottree()
        except lxml.etree.XMLSyntaxError:
            log.debug(traceback.format_exc())
            log.warn("badly structured HTML - using slower fallback parser")
            root = lxml.html.soupparser.fromstring(html).getroottree()

        """
        log.debug(' # parsed tree')
        log.debug(root.__class__)
        log.debug(etree.tostring(root))
        log.debug(' # # #')
        """
        return root

    @staticmethod
    def append_metadata(root,portlet):
        """ Alters both root and portlet.

        ElementTree root is added a /html/head/portlet tag with portlet
        metadata for the XSLT parser.

        Marionet portlet.session is updated to reflect the data.
        """
        #
        # base url
        #
        # by default use portlet session base
        #
        head_base = root.find('head/base')
        if head_base is not None:
            base = head_base.get('href')
            log.debug('found head base %s' % (base))
            portlet.session.set('base', base)
        #
        # namespace
        #
        if portlet:
            portlet.session.set('namespace', portlet.namespace())
        #
        # get xmlns
        #
        m = re.search('{(.*)}', root.getroot().tag ) # hackish ..
        if m:
            xmlns = m.group(1)
            log.debug('xmlns: '+xmlns)
        else:
            xmlns = ''
        #
        # append
        #
        head = root.find('//{%s}head' % xmlns)
        if head is not None:
            head.append(portlet.session)
            #
            # get title for portlet object.
            #
            title = head.find('{%s}title' % xmlns)
            if title is not None:
                # strip leading and trailing non-word chars
                portlet.title = re.sub(
                    r'^\W+|\W+$','',
                    title.text)
            """
            Get content_type and charset.
            Not used so commented out.

            _content = tree.findall('head/meta[@content]')
            if _content:
                (meta['content_type'],meta['charset']) = '; '.split(
                    _content[0].attrib['content'])
            """
        else:
            log.warn('OOPS no head!')

        """
        log.debug("portlet session: %s" % (etree.tostring(portlet.session)))
        log.debug(' # spiced tree')
        log.debug(etree.tostring(root))
        log.debug(' # # #')
        """
        return root

    @staticmethod
    def transform(html_tree,sheet='body'):
        """ Performs XSL transformation to HTML tree using sheet.
            @returns lxml.etree._XSLTResultTree
        """
        #log.debug(sheet+' xslt')
        xslt_tree = PageProcessor.getInstance().sheets[sheet]
        return etree.XSLT(xslt_tree)(
            html_tree,
            foo="'bar'")

    @staticmethod
    def process(html,portlet,**kwargs):
        """ Serializes the response body to a node tree,
            extracts metadata and transforms the portlet body.
            Context contains keys 'request' and 'response', where
            the request is the Portlet request and the response is
            the remote server response.

            @returns tuple (body,metadata)
        """
        #log.debug('processing response for portlet %s' % (portlet))
        tree = PageProcessor.parse_tree(html)
        #
        # add portlet metadata
        #
        PageProcessor.append_metadata(tree,portlet)

        html = str(
            PageProcessor.transform(tree,**kwargs))
        """
        log.debug(' # portlet html')
        log.debug(html)
        log.debug(' # # #')
        """
        return (html,{}) # meta is deprecated


    ### tag rewrites ###

    @staticmethod
    def link(obj,anchor,namespace,base=None):
        """ XXX: HACK """
        #portlet_url = urlparse("http://localhost:8000/hack")
        #print portlet_url
        #log.debug('anchor: %s' % etree.tostring(anchor[0]))
        # TODO: test "javascript:" and "#"
        
        path = '/hesari'
        
        href= anchor[0].get('href')
        if not href:
            return anchor
        
        #cgi.parse_qs(urlparse.urlsplit(foo).query)
        url_param = quote(
            href.encode('utf8'))
        query = '%s_href=%s' % (namespace, url_param)
        
        anchor[0].set('href', urlunsplit((
            'http',
            'localhost:8000',
            path,
            query,
            ''
            )))
        return anchor

    @staticmethod
    def href(obj,href,base=None):
        log.debug('parsing href "%s"' % (href))
        if base and not re.match('^http', href):
            log.debug('base: %s' % (base))
            """
            if re.match('^/', href):
                log.debug('absolute path')
                baseurl = urlparse(base)
                return urljoin(base+'/',href)
            else:
            """
            log.debug('relative path')
            join = urljoin(base+'/',href)
            #log.debug(join)
            img_url = re.sub('(?<!:)//', '/', join)
            #log.debug(img_url)
            return img_url
        else:
            log.warn('portlet has no base')
            return href

    @staticmethod
    def image(obj,img,base=None):
        """ Alters the img tag. """
        #log.debug('image: %s' % etree.tostring(img[0]))
        src = img[0].get('src')
        url = PageProcessor.href(None,src,base)
        img[0].set('src',url)
        return img

