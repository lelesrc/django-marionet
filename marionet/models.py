# -*- coding: utf-8 -*-
#
# In the works.

# django imports
from django import forms
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log, Config
from test.settings import DEBUG
log.setlevel('debug' if DEBUG else 'info')

import httpclient
from singletonmixin import Singleton
from lxml import etree
import lxml.html.soupparser
from StringIO import StringIO


class PortletFilter():
    """ This is still a mess. """
    @staticmethod
    def render_filter(view_func):
        """
        Filter for portlet render requests.

        By applying decorator @render_filter into Portlet methods,
        this will let the _filter() function to call the desired method
        with custom arguments.

        Returns a function.
        """
        #config = kwargs['config']
        #log.debug('config: %s' % (config))
        def _filter(ctx, *args, **kwargs):
            log.debug("render_filter activated")
            if not 'config' is kwargs:
                config = {'pi':3.14159}
                log.info("no config")
            else:
                config = kwargs['config']
                log.debug(config)

            request = None
            # hardwire config to context
            #log.debug(ctx)
            # oops!
            #ctx = RequestContext(request, config)
            #log.debug(ctx)
            return view_func(ctx,config,*args,**kwargs)

        _filter.__name__ = view_func.__name__
        _filter.__dict__ = view_func.__dict__
        _filter.__doc__  = view_func.__doc__

        return _filter

class MarionetFilter(PortletFilter):
    """ Not used. """
    def __init__(self, *args, **kwargs):
        Portlet.__init__(self)
        log.info("Marionet '%s' version %s" % ('',self.VERSION))

class Marionet(Portlet):
    """ This is still a mess.
    """
    VERSION = '0.0.1'

    url        = models.TextField(u"url",        blank=True)
    req_method = models.TextField(u"req_method", blank=True)
    referer    = models.TextField(u"referer",    blank=True)

    # session secret for security given at init, not stored to DB
    session_secret = None
    
    # uhm..
    __portlet_filter__ = None

    def __unicode__(self):
        return "%s" % self.url

    def __init__(self, *args, **kwargs):
        Portlet.__init__(self)
        log.info("Marionet '%s' version %s" % ('',self.VERSION))

        if 'session_secret' in kwargs:
            self.session_secret = kwargs['session_secret']

    def __config__(self):
        """ Portlet should handle conf from text file """
        log.debug("__config__")
        return {'url': 'http://0.0.0.0:8000/test'}

    def my_render_filter(self,*args,**kwargs):
        """ Loaded apparently only once at startup. """
        log.debug(" -- PREFILTER -- ") # the message never appers
        #print "ehm" # well but this does, at startup
        #kwargs['config'] = {'hm':0} # need to think of passing config
        
        return PortletFilter.render_filter(self,*args,**kwargs)

    @my_render_filter
    def render(self, context=None):
        """
        """
        # HACK to circumvent render filter
        url = 'http://localhost:3000/caterpillar/test_bench'

        log.info("render "+url)
        log.debug(context)
        client = WebClient()
        response = client.get(url)
        (out,meta) = PageProcessor.process(response,sheet='body')
        #log.debug(out)
        return out

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

        #self.__config = httpclient.Configuration()
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

    def __body_xslt(self):
        """ Define body transformation stylesheet.
        """
        log.debug('define xslt - this message should only appear at startup')
        return etree.XML('''\
<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
     <xsl:output method="html"/>

     <xsl:param name="namespace" required="yes"/>

     <xsl:template match="html">
         <div id="{$namespace}_body">
            <xsl:apply-templates select="body"/>
         </div>
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
        """
        In case the input is badly formatted html, the soupparser is used.
        """
        html = response.read()
        try:
            root = etree.parse(
                StringIO(
                    html
                    ))
        except lxml.etree.XMLSyntaxError:
            log.warn("badly structured HTML - using slower fallback parser")
            root = lxml.html.soupparser.fromstring(html)
        return root

    @staticmethod
    def transform(html_tree,sheet='body'):
        """ Performs XSL transformation to HTML tree using sheet.
        """
        log.debug(sheet+' xslt')
        xslt_tree = PageProcessor.getInstance().sheets[sheet]
        return etree.XSLT(xslt_tree)(
            html_tree,
            namespace="'__namespace__'"
            )

    @staticmethod
    def process(response,*args,**kwargs):
        """ Serializes the response body to a node tree,
        extracts metadata and transforms the portlet body.
        Returns a tuple of (body,metadata).
        """
        tree = PageProcessor.parse_tree(response)
        meta = {
            'title': "",
            #'content_type': None,
            #'charset': None,
            }
        meta['title'] = tree.findtext('head/title')
        # get content_type and charset
        """ Not used so commented out.
        _content = tree.findall('head/meta[@content]')
        if _content:
            (meta['content_type'],meta['charset']) = '; '.split(
                _content[0].attrib['content'])
        """
        log.debug('meta: %s' % (meta))
        return (PageProcessor.transform(tree,*args,**kwargs),meta)

