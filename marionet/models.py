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

class PortletFilter():
    """
    Embodies a state in __config, that is loaded only once during startup.
    """
    __config = {'pi': 3.14}
    #__metaclass__ = metaclass.SingletonMetaClass

    def __init__(self):
        log.debug("RenderFilter initialized")

    @staticmethod
    def render_filter(view_func):
        """
        Filter for portlet render requests.

        By applying decorator @render_filter into Portlet methods,
        this will let the _filter() function to call the desired method
        with custom arguments.

        Returns a function.
        """
        def _filter(this, *args, **kwargs):
            log.debug("render_filter activated")
            request = None
            # hardwire config to context
            ctx = RequestContext(request, PortletFilter.__config)
            #log.debug(ctx)
            return view_func(this, ctx)

        _filter.__name__ = view_func.__name__
        _filter.__dict__ = view_func.__dict__
        _filter.__doc__  = view_func.__doc__

        return _filter


class Marionet(Portlet):
    """A simple portlet to display some text.
    """
    VERSION = '0.0.1'

    url        = models.TextField(u"url",        blank=True)
    req_method = models.TextField(u"req_method", blank=True)
    referer    = models.TextField(u"referer",    blank=True)

    # session secret for security given at init, not stored to DB
    session_secret = None

    def __unicode__(self):
        return "%s" % self.url

    def __init__(self, *args, **kwargs):
        log.info("Marionet '%s' version %s" % ('',self.VERSION))
        if 'session_secret' in kwargs:
            self.session_secret = kwargs['session_secret']

    @PortletFilter.render_filter
    def render(self, context):
        """Renders the portlet as HTML.
        """
        #log.debug(context)
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
