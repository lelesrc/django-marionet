# -*- coding: utf-8 -*-
#
#

# django imports
from django import forms
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log, Config
import httpclient


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
        print "config"
        return {'url': 'http://0.0.0.0:8000/test'}

    def my_render_filter(self,*args,**kwargs):
        """ Loaded apparently only once at startup. """
        log.debug(" -- PREFILTER -- ") # the message never appers
        print "ehm" # well but this does, at startup
        #kwargs['config'] = {'hm':0} # need to think of passing config
        
        return PortletFilter.render_filter(self,*args,**kwargs)

    @my_render_filter
    def render(self, context=None):
        """
        """
        log.debug(" -- RENDER -- ")
        #log.debug(self)
        log.debug(context)
        #request = context.get("request")
        #url = #get from context
        #log.debug("View "+url)
        return context.__str__

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
        #print "Stored cookies: %s" % (self.cookies)

    def add_cookies(self,cookies):
        """ Add cookies from dict.
        Format: {'foo': ['foo=bar'], 'baz': ['baz=xyz']}
        """
        self.cookies.update(cookies)

    def cookie_headers(self):
        """ Parse cookies to HTTP header string. 
        """
        #print "%i cookies" % (len(self.cookies))
        return '; '.join(map(lambda f: f[0], self.cookies.values()))

    def get(self,url,referer=None):
        """ Execute GET request.
        Returns httplib.HTTPResponse.
        """
        method = httpclient.GetMethod(url)
        # add cookies
        method.add_request_header('Cookie',self.cookie_headers())
        #print method.getheaders()
        method.execute()
        response = method.get_response()
        #print response.getheaders()
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
        #print method.getheaders()
        method.execute()
        response = method.get_response()
        #print response.getheaders()
        # server redirect does not echo sent cookies, but may set new ones
        self.update_cookies(response) # updates state
        # follow redirect..
        if response.status == 302 or response.status == 301:
            return self.get(response.getheader('Location'))
        else:
            return response


class XSLTransformer():
    """ Singleton.
    Loads XSLT sheets.
    """
    sheets = None

    def __init__(self,*args,**kwargs):
        """ Define xslts. 
        """
        self.sheets = {'body': self.__body_xslt()}

    def __body_xslt(self):
        """ TODO
        """
        log.debug('load xslt from file')
        return "<>"


class XSLTfuncs():
    """ Functions for XSL transformation.
    """
    @staticmethod
    def transform(doc,sheet='body'):
        """ Performs XSL transformation to doc using sheet.
        """
        log.debug('transform body of doc')
        
        xslt = XSLTransformer().sheets[sheet]
        log.debug(xslt)
        return doc


### TEXT PORTLET (useful to study how it works)

class TextPortlet(Portlet):
    """A simple portlet to display some text.
    TextPortlet copied from django-portlets (BSD license)
    author: diefenbach
    """
    text = models.TextField(_(u"Text"), blank=True)

    def __unicode__(self):
        return "%s" % self.id

    def render(self, context=None):
        """Renders the portlet as html.
        """
        return render_to_string("portlets/text_portlet.html", {
            "title" : self.title,
            "text" : self.text
        })

    def form(self, **kwargs):
        """
        """
        return TextPortletForm(instance=self, **kwargs)

class TextPortletForm(forms.ModelForm):
    """Form for the TextPortlet.
    """
    class Meta:
        model = TextPortlet

register_portlet(TextPortlet, "TextPortlet")
