# -*- coding: utf-8 -*-
#
# In the works.

# django imports
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.http import QueryDict
from django.template import RequestContext
from django.template.loader import render_to_string

from portlets.models import Portlet, PortletRegistration
from portlets.utils import register_portlet

from portlets.models import PortletSession

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
        XXX: is this really needed?
    """
    portlet = models.ForeignKey('Marionet')

    def instance_id(self):
        return '%s_INSTANCE_%s' % (self.portlet.id, self.id)

    def elem(self):
        elem = etree.Element("portlet-preferences")
        elem.set('portlet_id', '%s' % (self.portlet.id))
        elem.set('instance_id', '%s' % (self.instance_id()))
        return elem

    def tag(self):
        return etree.tostring(self.elem())


class PortletURL():
    """
    Liferay example:
    http://example.com/web/some-group/some-page?p_p_id=wb_profile_INSTANCE_ciio&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-2&p_p_col_count=2
    """
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
        if self.query is None:
            qs = ''
        else:
            qs = "&".join(map(lambda (k,v): '%s=%s' % (
                k,quote(v.encode('utf8'))),
                self.query.items()))
        if self.location is None:
            log.warn('portlet context has no location')
            url = '?'+qs
        else:
            url = urlunsplit((
                self.location.scheme,
                self.location.netloc,
                self.location.path,
                qs,
                ''
                ))
        return url

    @staticmethod
    def render_url(
        location,
        query,
        namespace=None,
        href=None,
        params={},
        method='GET'
        ):
        """ location = ParseResult
            query = QueryDict
        """
        log.debug('portlet href: %s' % (href))
        log.debug(location)
        if href is None:
            return PortletURL(location, query)
        if namespace is None:
            log.warn('Portlet namespace is undefined')
            return PortletURL(location, query)

        # append portlet parameters to query
        # - since query is immutable, create a copy if needed
        _query = copy(query)
        log.debug('context query: %s' % (_query))
        _query.__setitem__(namespace+'.href', href)

        return PortletURL(location, _query)

    @staticmethod
    def action_url(*args):
        ''' UNIMPLEMENTED '''
        raise NotImplemented

    @staticmethod
    def resource_url(*args):
        ''' UNIMPLEMENTED '''
        raise NotImplemented


class PortletFilter():

    @staticmethod
    def render_filter(view_func):
        """
        Filter for portlet render requests.

        If the context url contains a new href for this portlet
        instance, the portlet.url is updated.
        """
        def do_filter(portlet, context):
            """ Prepares the portlet by preprocessed context
            """ 
            log.debug(' * * * render filter activated')
            # by default, use GET
            portlet.session.set('method', 'GET')
            #
            ### match portlet query directive
            #
            query = context.get('query')
            for key in query.keys():
                namespace = portlet.session.get('namespace')
                m = re.match('%s\.(.*)' % namespace, key)
                directive = m.group(1)
                log.debug(' * '+namespace+' '+directive)
                if directive == 'href':
                    href = query.__getitem__(key)
                    #log.debug('portlet href: %s' % (href))
                    # rewrite url
                    base = portlet.session.get('baseURL')
                    url = PageProcessor.href(None,href,base)
                    # update portlet
                    portlet.url = unquote(url)
                    log.debug('new url: %s' % (portlet.url))
                    # XXX: delete method
                elif directive == 'action':
                    action = query.__getitem__(key)
                    log.debug('portlet action '+action)
                    if action == 'process':
                        portlet.session.set('method', 'POST')
                        # portlet query string from request.POST
                        portlet.session.set('qs', context.get('post').urlencode())

            else:
                pass
                #log.debug('no query parameters')

            return view_func(portlet,context)

        do_filter.__name__ = view_func.__name__
        do_filter.__dict__ = view_func.__dict__
        do_filter.__doc__  = view_func.__doc__

        return do_filter


class Marionet(Portlet):
    """ A new session is always created.
    """
    VERSION = '0.0.1'

    url = models.URLField(null=True)
    # holder for user session for the render phase, not stored to database
    session = None

    def __init__(self, *args, **kwargs):
        #log.debug('initializing marionet: '+str(kwargs))
        if 'session' in kwargs:
            session = kwargs.pop('session')
            if isinstance(session, PortletSession):
                log.debug('marionet ~ prepared session')
                self.session = session
            elif session is True:
                log.debug('marionet ~ new session')
                # session requested, create volatile
                self.session = MarionetSession(*args,**kwargs)
        super(Marionet, self).__init__(
            *args,
            **kwargs
            )
        ### set state up-to-date
        if self.session:
            # Marionet
            if not self.url:
                self.url = self.session.get('url')
            # MarionetSession
            #
            # baseURL
            if self.session.get('baseURL') is None:
                if self.url is not None:
                    _url = urlparse(self.session.get('url'))
                    self.session.set('baseURL',
                        '%s://%s' % (_url.scheme, _url.netloc))

        log.info(self.__unicode__())
        #log.info("Marionet %s: %s, session %s" % (self.id,self.url,self.session.name))
        #log.info(self.session)

    def __unicode__(self):
        if self.session:
            return 'marionet_%s.%s.%s' % (self.id, self.session.name, self.url)
        else:
            return 'marionet_%s.%s' % (self.id, self.url)

    @PortletFilter.render_filter
    def render(self, context):
        """ Render GET.

            This method has side effects; the self.title is set only
            after render() is called, but currently the portlet title
            is inserted to the page before rendering, thus the title
            is empty...
        """
        log.info(" * * * render * "+self.url)
        #log.debug('context: %s' % (context))

        ### update session
        # context location
        if context['location'] is not None:
            self.session.set('location',
                urlunparse(context['location']))
        # context query
        if context['query'] is not None:
            self.session.set('query',
                context['query'].urlencode())
        #log.debug(self.session)

        try:
            client = WebClient()
            ### select method and exec request
            if self.session.get('method') == 'GET':
                response = client.get(self.url)
            if self.session.get('method') == 'POST':
                params = QueryDict(self.session.get('qs'))
                response = client.post(self.url, params)

            ### process the response . .
            #
            # in this portlet context
            self.context = context
            # process alters the state of session
            # as, fe. html/head may contain <base>
            out = PageProcessor.process(
                response,
                self.session,
                sheet='body')
            # get title from page
            if not self.title:
                if self.session.get('title'):
                    self.title = self.session.get('title')
                    log.info('title: '+self.title)
            log.info('Page length: %i bytes' % (len(out)))
            return out
        except:
            log.error(traceback.format_exc())
            return "ERROR"

    def render_url(self, href, params={}):
        """ Returns a PortletURL.render_url.
            Call the result object to get string representation of the url.
            XXX: is this needed?
        """
        log.debug(self.session)
        return PortletURL.render_url(
            method    = 'GET',
            location  = self.context.get('location'),
            query     = self.context.get('query'),
            href      = href,
            params    = params,
            namespace = self.session.get('namespace'),
            )

    def action_url(self, href, params={}):
        ''' UNIMPLEMENTED '''
        pass
        
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


class MarionetSession(PortletSession):
    """ Connects marionet and a user,
        so a single portlet can be created on the page,
        and all users accessing have their own session.
    """
    user = models.ForeignKey(User, null=True, unique=True)
    portlet = models.ForeignKey(Marionet, null=True)
    cookie = '' # TODO: store to database

    def __unicode__(self):
        return 'MarionetSession %s for user %s with marionet %s ' % (
            self.id, self.user_id, self.portlet_id)


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
        if referer is not None:
            method.add_request_header('Referer',referer)
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
        name="location"
        select="//*[local-name()='head']/portlet-session/@location" />

    <xsl:variable
        name="query"
        select="//*[local-name()='head']/portlet-session/@query" />

    <xsl:variable
        name="namespace"
        select="//*[local-name()='head']/portlet-session/@namespace" />

    <xsl:variable
        name="base"
        select="//*[local-name()='head']/portlet-session/@baseURL" />


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
        <xsl:copy-of select="marionet:link(.,string($location),string($query),string($namespace),string($base))"/>
    </xsl:template>

    <!-- Rewrite image references -->
    <xsl:template match="img">
      <xsl:copy-of select="marionet:image(.,string($base))"/>
    </xsl:template>

    <!-- Convert link tags in head to style tags -->
    <xsl:template match="*[local-name()='html']/head/link">
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
    def append_metadata(root,session):
        """ Updates both root and portlet session state.

        For XSLT parser to obtain local variables,
        a MarionetSession etree.Element is appended
        to /html/head/portlet-session.

        MarionetSession session, as a side-effect, is a
        updated to reflect html metadata.
        * base => @baseURL
        * title
        * 
        """
        #
        # get xmlns
        #
        m = re.search('{(.*)}', root.getroot().tag ) # hackish ..
        if m:
            xmlns = m.group(1)
            #log.debug('xmlns: '+xmlns)
        else:
            xmlns = ''
        #
        # resolve head
        #
        head = root.find('{%s}head' % xmlns)
        if head is None:
            log.warn('OOPS no head!')
            # create new head into root
            head = etree.Element('head')
            root.getroot().append(head)
        #
        # base url
        #
        head_base = head.find('base')
        if head_base is not None:
            base = head_base.get('href')
            log.debug('found head base %s' % (base))
            session.set('baseURL', base)
        #
        # title
        #
        title = head.find('{%s}title' % xmlns)
        if title is not None:
            # strip leading and trailing non-word chars
            session.set('title', re.sub(
                r'^\W+|\W+$','',
                title.text))
        """
        Get content_type and charset.
        Not used so commented out.

        _content = tree.findall('head/meta[@content]')
        if _content:
            (meta['content_type'],meta['charset']) = '; '.split(
                _content[0].attrib['content'])
        """
        #
        # append
        #
        head.append(session._Element)

        """
        log.debug(' # new head')
        log.debug(etree.tostring(head))
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
#            foo="'bar'"  # XXX insert XSLT variables, remember if needed
            )
    @staticmethod
    def process(html,session,**kwargs):
        """ Serializes the response body to a node tree,
            extracts metadata and transforms the portlet body.
            Context contains keys 'request' and 'response', where
            the request is the Portlet request and the response is
            the remote server response.

            @returns tuple (body,metadata)
        """
        #log.debug('processing response for portlet %s' % (portlet))
        tree = PageProcessor.parse_tree(html)

        # add portlet metadata
        #
        PageProcessor.append_metadata(tree,session)

        # execute XSLT and collect metadata
        #
        html = str(PageProcessor.transform(tree,**kwargs))
        """
        log.debug(' # portlet html')
        log.debug(html)
        log.debug(' # # #')
        """
        return html


    ### ### tag rewrite functions

    @staticmethod
    def link(obj,anchor,location,query,namespace,base=None):
        """ Ordinary hyperlink.
        
            TODO: test "javascript:" and "#"
        """
        log.debug('anchor: %s' % etree.tostring(anchor[0]))

        href = anchor[0].get('href')
        if not href:
            return anchor

        if base is not None:
            # rewrite url
            href = PageProcessor.href(None,href,base)

        url = PortletURL.render_url(
            location = urlsplit(location),
            query = QueryDict(query),
            namespace = namespace,
            href = href,
            params = {},
            method = 'GET'
            )

        anchor[0].set('href', url.__unicode__())
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
            _url = re.sub('(?<!:)//', '/', join)
            #log.debug(_url)
            return _url
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

