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

import logging
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
            logging.warn('portlet context has no location')
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
        logging.debug('portlet href: %s' % (href))
        logging.debug(location)
        if href is None:
            return PortletURL(location, query)
        if namespace is None:
            logging.warn('Portlet namespace is undefined')
            return PortletURL(location, query)

        # append portlet parameters to query
        # - since query is immutable, create a copy if needed
        _query = copy(query)
        _query.__setitem__(namespace+'.href', href)
        logging.debug('context query: %s' % (_query))

        return PortletURL(location, _query)

    @staticmethod
    def action_url(
        location,
        query,
        namespace=None,
        href=None,
        params={},
        method='POST'
        ):
        """ @param location = ParseResult
            @param query = QueryDict
        """
        logging.debug('action href: %s' % (href))
        logging.debug(location)
        if href is None:
            return PortletURL(location, query)
        if namespace is None:
            logging.warn('Portlet namespace is undefined')
            return PortletURL(location, query)

        # append portlet parameters to query
        # - since query is immutable, create a copy if needed
        _query = copy(query)
        _query.__setitem__(namespace+'.href', href)
        _query.__setitem__(namespace+'.action', 'process')
        logging.debug('context query: %s' % (_query))

        return PortletURL(location, _query)


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
            logging.debug(' * * * render filter activated')
            #
            ### session defaults
            #
            # use GET
            portlet.session.set('method', 'GET')
            # no XHR
            portlet.session.set('xhr', '0')
            #
            ### match portlet query directive
            #
            query = context.get('query')
            for key in query.keys():
                namespace = portlet.session.get('namespace')
                match = re.match('%s\.(.*)' % namespace, key)
                if match is not None:
                    directive = match.group(1)
                    logging.debug(' * '+namespace+' '+directive)
                    ### set URL
                    if directive == 'href':
                        href = query.__getitem__(key)
                        # rewrite url
                        base = portlet.session.get('baseURL')
                        url = PageProcessor.href(None,href,base)
                        # update portlet
                        portlet.url = unquote(url)
                        logging.debug('new url: %s' % (portlet.url))
                    elif directive == 'action':
                        action = query.__getitem__(key)
                        logging.debug('portlet action '+action)
                        ### POST
                        if action == 'process':
                            portlet.session.set('method', 'POST')
                            # portlet query string from request.POST
                            portlet.session.set('qs', context.get('post').urlencode())
                    ### XHR
                    elif directive == 'xhr':
                            portlet.session.set('xhr', '1')

            else:
                pass
                #logging.debug('no query parameters')

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
        #logging.debug('initializing marionet: '+str(kwargs))
        if 'session' in kwargs:
            session = kwargs.pop('session')
            if isinstance(session, PortletSession):
                logging.debug('marionet ~ prepared session')
                self.session = session
            elif session is True:
                logging.debug('marionet ~ new session')
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

        logging.info(self.__unicode__())
        #logging.info("Marionet %s: %s, session %s" % (self.id,self.url,self.session.name))
        #logging.info(self.session)

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
        logging.info(" * * * render * "+self.url)
        #logging.debug('context: %s' % (context))

        ### update session
        # context location
        if context['location'] is not None:
            self.session.set('location',
                urlunparse(context['location']))
        # context query
        if context['query'] is not None:
            self.session.set('query',
                context['query'].urlencode())
        # baseURL
        # XXX: security! shall we let the user go beyond the first set domain?
        if self.url is not None:
            _url = urlparse(self.url)
            self.session.set('baseURL',
                '%s://%s' % (_url.scheme, _url.netloc))
        #logging.debug(self.session)

        try:
            client = WebClient()
            ### select method and exec request
            # GET
            if self.session.get('method') == 'GET':
                response = client.get(self.url,
                    headers={'xhr': self.session.get('xhr')})
            # POST
            elif self.session.get('method') == 'POST':
                response = client.post(self.url,
                    params=self.session.get('qs'),
                    headers={'xhr': self.session.get('xhr')})

            if response.status != 200:
                return '%s %s' % (response.status, response.reason)

            # XXX: do not process XHR
            if self.session.get('xhr') == 1:
                return response.read()

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
                    logging.info('title: '+self.title)
            logging.info('Page length: %i bytes' % (len(out)))
            #self.session.save()
            return out
        except:
            logging.error(traceback.format_exc())
            return "ERROR"

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
    # user is not necessary, and each user may have multiple sessions
    user = models.ForeignKey(User, null=True, unique=False)
    # portlet is not necessary, if initialized with url kwarg.
    portlet = models.ForeignKey(Marionet, null=True)
    # key is needed to identify, if user is not set.
    django_key = models.CharField(null=True, blank=True, max_length=42, unique=False)

    def __unicode__(self):
        return 'MarionetSession %s for user %s (key %s) with marionet %s ' % (
            self.id, self.user, self.django_key, self.portlet_id)

    def clean(self):
        """ Validation.
        """
        #from django.core.exceptions import ValidationError
        if not self.user and not self.django_key:
            #raise ValidationError('No user nor key.')
            self.django_key = 'anon_shared'


class WebClient():
    """ Modeled after OnlineClient in html2jsr286.
        Handles state maintenance, in that after each request
        cookies are updated.
    """

    def __init__(self,*args,**kwargs):
        """ Store cookies to the instance. """
        if 'cookies' in kwargs:
            self.cookies = kwargs.pop('cookies')
        else:
            self.cookies = {}

        self.__config = httpclient.Configuration()
        self.__config.set_user_agent(
            '# Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100130 Gentoo Firefox/3.6')

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
            logging.debug("Stored %i cookies: %s" % (len(self.cookies),self.cookies))

    def add_cookies(self,cookies):
        """ Add cookies from dict.
            Format: {'foo': ['foo=bar'], 'baz': ['baz=xyz']}
        """
        self.cookies.update(cookies)

    def cookie_headers(self):
        """ Parse cookies to HTTP header string. 
        """
        return '; '.join(map(lambda f: f[0], self.cookies.values()))

    def get(self,url,**kwargs):
        """ Executes GET request.

            @returns httplib.HTTPResponse.
        """
        logging.info('GET %s' % (url))
        method = httpclient.GetMethod(url,**kwargs)

        # add cookies
        method.set_request_header('Cookie',self.cookie_headers())
#        if referer is not None:
#            method.set_request_header('Referer',referer) # XXX
        #logging.debug(method.getheaders())
        method.execute()
        response = method.get_response()
        #logging.debug(response.getheaders())
        self.update_cookies(response) # updates state
        return response

    def post(self,url,params='',**kwargs):
        """ Executes POST request.

            @param params is an urlencoded string.
            @returns httplib.HTTPResponse.
        """
        method = httpclient.PostMethod(url,**kwargs)

        # add parameters to request body
        method.set_body(params)
        # add cookies
        method.set_request_header('Cookie',self.cookie_headers())
        # httpclient forgets cookies with automatic redirect..
        method.set_follow_redirects(0)
        #logging.debug(method.getheaders())
        method.execute()
        response = method.get_response()
        #logging.debug(response.getheaders())
        # server redirect does not echo sent cookies, but may set new ones
        self.update_cookies(response) # updates state
        # follow redirect..
        if response.status == 302 or response.status == 301:
            return self.get(response.getheader('Location'), **kwargs) # XXX
            # maybe it is too dangerous to GET with all kwargs, should pick
            # up just "headers['xhr']" if it exists.. 
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
        ns['form'] = PageProcessor.form


    def __body_xslt(self):
        """ Define body transformation stylesheet.
        """
        logging.debug('define xslt - this message should only appear at startup')
        logging.warn('DEPRECATED inline XSLT -- use external file from now on')
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

    <xsl:template match="*[local-name()='body']">
        <xsl:apply-templates select="node()"/>
    </xsl:template>

    <!-- Rewrite links -->
    <xsl:template match="*[local-name()='a']">
        <xsl:copy-of select="marionet:link(.,string($location),string($query),string($namespace),string($base))"/>
    </xsl:template>

    <!-- Rewrite image references -->
    <xsl:template match="*[local-name()='img']">
      <xsl:copy-of select="marionet:image(.,string($base))"/>
    </xsl:template>

    <!-- Convert link tags in head to style tags -->
    <xsl:template match="*[local-name()='html']/head/link">
        <style type="text/css" id="{@id}">
        @import "<xsl:value-of select="marionet:href(string(@href),string($base))"/>";
        </style>
    </xsl:template>

    <!-- Form POST action -->
    <xsl:template match="*[local-name()='form']">
        <xsl:copy-of select="marionet:form(.,string($location),string($query),string($namespace),string($base))"/>
    </xsl:template>

    <!-- Copy through everything that hasn't been modified by the processor -->
    <xsl:template match="text()|@*|*">
        <xsl:copy>
          <xsl:apply-templates select="*|@*|text()"/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>''')


    @staticmethod
    def process(html,session,**kwargs):
        """ Serializes the response body to a node tree,
            extracts metadata and transforms the portlet body.
            Context contains keys 'request' and 'response', where
            the request is the Portlet request and the response is
            the remote server response.

            @returns string html
        """
        #logging.debug('processing response for portlet %s' % (portlet))
        tree = PageProcessor.parse_tree(html)

        # add portlet metadata
        #
        PageProcessor.append_metadata(tree,session)

        # execute XSLT and collect metadata
        #
        html = str(PageProcessor.transform(tree,**kwargs))
        """
        logging.debug(' # portlet html')
        logging.debug(html)
        logging.debug(' # # #')
        """
        return html


    @staticmethod
    def transform(html_tree,sheet='body'):
        """ Performs XSL transformation to HTML tree using sheet.
            @returns lxml.etree._XSLTResultTree
        """
        #logging.debug(sheet+' xslt')
        xslt_tree = PageProcessor.getInstance().sheets[sheet]
        return etree.XSLT(xslt_tree)(
            html_tree,
#            foo="'bar'"  # XXX insert XSLT variables, remember if needed
            )


    @staticmethod
    def parse_tree(response):
        """ Parses the response HTML.
            In case the input is badly formatted HTML, the soupparser is used.
        """
        html = response.read() # XXX read() in static method XXX
        """
        logging.debug(' # input HTML')
        logging.debug(html)
        logging.debug(' # # #')
        """
        try:
            root = etree.fromstring(html).getroottree()
        except lxml.etree.XMLSyntaxError:
            logging.debug(traceback.format_exc())
            logging.warn("badly structured HTML - using slower fallback parser")
            root = lxml.html.soupparser.fromstring(html).getroottree()

        """
        logging.debug(' # parsed tree')
        logging.debug(root.__class__)
        logging.debug(etree.tostring(root))
        logging.debug(' # # #')
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
            #logging.debug('xmlns: '+xmlns)
        else:
            xmlns = ''
        #
        # resolve head
        #
        head = root.find('{%s}head' % xmlns)
        if head is None:
            logging.warn('OOPS no head!')
            # create new head into root
            head = etree.Element('head')
            root.getroot().append(head)
        #
        # base url
        #
        head_base = head.find('base')
        if head_base is not None:
            base = head_base.get('href')
            logging.debug('found head base %s' % (base))
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
        logging.debug(' # new head')
        logging.debug(etree.tostring(head))
        logging.debug(' # # #')
        """
        return root


    ### ### tag rewrite functions

    @staticmethod
    def link(obj,anchor,location,query,namespace,base=None):
        """ Ordinary hyperlink.
        
            TODO: test "javascript:" and "#"
        """
        logging.debug('anchor: %s' % etree.tostring(anchor[0]))

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
    def form(obj,form,location,query,namespace,base=None):
        logging.debug('form: %s' % etree.tostring(form[0]))
        action = form[0].get('action')
        if not action:
            return form
        if base is not None:
            action = PageProcessor.href(None,action,base)

        url = PortletURL.action_url(
            location = urlsplit(location),
            query = QueryDict(query),
            namespace = namespace,
            href = action,
            params = {}, # got from form?
            method = 'POST'
            )

        form[0].set('action', url.__unicode__())
        return form

    @staticmethod
    def href(obj,href,base=None):
        """ Parses base into href to form a complete url.
        """
        logging.debug('parsing href "%s"' % (href))
        if not re.match('^http', href):
            if base:
                #logging.debug('base: %s' % (base))
                """
                if re.match('^/', href):
                    logging.debug('absolute path')
                    baseurl = urlparse(base)
                    return urljoin(base+'/',href)
                else:
                """
                #logging.debug('relative path')
                join = urljoin(base+'/',href)
                _url = re.sub('(?<!:)//', '/', join)
                #logging.debug(_url)
                return _url
            else:
                logging.warn('portlet has no base')
        return href

    @staticmethod
    def image(obj,img,base=None):
        """ Alters the img tag. """
        #logging.debug('image: %s' % etree.tostring(img[0]))
        src = img[0].get('src')
        url = PageProcessor.href(None,src,base)
        img[0].set('src',url)
        return img

