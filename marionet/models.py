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

import re
import httpclient
from singletonmixin import Singleton
from lxml import etree
import lxml.html.soupparser
from StringIO import StringIO
from urlparse import urlparse


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
        def _filter(ctx, *args, **kwargs):
            log.debug("---------------------------------------------------")
            if not 'config' is kwargs:
                config = {'pi':3.1415926535897932384626}
            else:
                config = kwargs['config']

            log.debug("context: %s\nconfig: %s" % (ctx,config))

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
        if 'session_secret' in kwargs:
            self.session_secret = kwargs['session_secret']
            del kwargs['session_secret']
        Portlet.__init__(self, *args, **kwargs)
        log.info("Marionet '%s' version %s" % (self.title,self.VERSION))

    def __config__(self):
        """ Portlet should handle conf from text file """
        log.debug("__config__")
        return {'url': 'http://0.0.0.0:8000/test'}

    def namespace(self):
        return '__portlet_%s__' % (self.id)

    def my_render_filter(self,*args,**kwargs):
        """ Loaded apparently only once at startup. """
        #log.debug(" -- PREFILTER -- ")
        #kwargs['config'] = {'hm':0} # need to think of passing config
        
        return PortletFilter.render_filter(self,*args,**kwargs)

    @my_render_filter
    def render(self, context=None):
        """
        """
        log.debug("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV")
        log.info("render "+self.url)
        log.debug(context)
        try:
            client = WebClient()
            response = client.get(self.url)
            (out,meta) = PageProcessor.process(self,response,sheet='body')
            #log.debug(out)
            self.title = meta['title'] # OOPS!
            #log.debug('title: '+self.title)
            """
            This method has side effects; the self.title is set only
            after render() is called, but currently the portlet title
            is inserted to the page before rendering, thus the title
            is empty...
            """
            return out
        except:
            log.error('processing failed')
            import traceback
            log.error(traceback.format_exc())
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


    def __body_xslt(self):
        """ Define body transformation stylesheet.
        """
        log.debug('define xslt - this message should only appear at startup')
        return etree.XML('''\
<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:marionet="http://github.com/youleaf/django-marionet"
     >
     <xsl:output method="html"/>

     <xsl:variable
        name="namespace"
        select="/html/head/portlet/@namespace" />

     <xsl:variable
        name="base"
        select="/html/head/portlet/@base" />

     <xsl:template match="/html/body">
         <div id="{$namespace}_body">
           <xsl:apply-templates select="node()"/>
         </div>
     </xsl:template>

    <!-- Rewrite image references -->
    <xsl:template match="img">
      <xsl:copy-of select="marionet:image(.,string($base))"/>
    </xsl:template>

    <!-- Copy through everything that hasn't been modified by the processor -->
    <xsl:template match="text()|@*|*">
        <xsl:copy>
          <xsl:apply-templates select="*|@*|text()"/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>''')


    @staticmethod
    def parse_tree(portlet,response):
        """
        Parses the response HTML.
        In case the input is badly formatted HTML, the soupparser is used.
        Inserts portlet meta data into /HTML/HEAD for XSLT parser.
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
        # append portlet metadata to /HTML/HEAD
        if portlet:
            url = urlparse(portlet.url)
            base = '%s://%s' % (url.scheme, url.netloc)
            log.debug("base url: %s" % (base))
            portlet_tag = etree.Element("portlet",
                namespace = portlet.namespace(),
                base = base
                )
            root.find('head').append(portlet_tag)
        return root

    @staticmethod
    def transform(html_tree,sheet='body'):
        """ Performs XSL transformation to HTML tree using sheet.
        @returns	lxml.etree._XSLTResultTree
        """
        log.debug(sheet+' xslt')
        xslt_tree = PageProcessor.getInstance().sheets[sheet]
        return etree.XSLT(xslt_tree)(html_tree)

    @staticmethod
    def process(portlet,response,*args,**kwargs):
        """ Serializes the response body to a node tree,
        extracts metadata and transforms the portlet body.
        Returns a tuple of (body,metadata).
        """
        log.debug('processing response for portlet %s' % (portlet))
        tree = PageProcessor.parse_tree(portlet,response)
        meta = {
            'title': "",
            #'content_type': None,
            #'charset': None,
            }
        try:
            # get title,
            # strip leading and trailing non-word chars
            meta['title'] = re.sub(
                r'^\W+|\W+$','',
                tree.findtext('head/title'))
        except TypeError:
            pass
        # get content_type and charset
        """ Not used so commented out.
        _content = tree.findall('head/meta[@content]')
        if _content:
            (meta['content_type'],meta['charset']) = '; '.split(
                _content[0].attrib['content'])
        """
        log.debug('meta: %s' % (meta))
        html = str(
            PageProcessor.transform(tree,*args,**kwargs))
        log.debug('processing of portlet %s complete' % (portlet))
        return (html,meta)


    ### tag rewrites ###

    @staticmethod
    def link(obj,url,base=None):
        log.debug('link: %s' % url)
        # TODO: test "javascript:" and "#"
        return None

    @staticmethod
    def image(obj,img,base=None):
        """ Alters the tag. """
        log.debug('image: %s' % etree.tostring(img[0]))

        src = img[0].get('src')
        if not re.match('^http', src):
            log.debug('relative url')
            log.debug('base: %s' % base)
            if base:
                img[0].set('src',base+src)

        return img
