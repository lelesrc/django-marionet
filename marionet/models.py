# -*- coding: utf-8 -*-
#
#

# django imports
from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log, Config

def portlet_filter(function=None):
    """
    Filter for portlet requests.
    http://passingcuriosity.com/2009/writing-view-decorators-for-django/
    """
    def _dec(view_func):
        def _filter(request, *args, **kwargs):
            log.debug("portlet_filter activated")
            #log.info(request.user)
            #log.info(request.REQUEST)
            return view_func(request, *args, **kwargs)

        _filter.__name__ = view_func.__name__
        _filter.__dict__ = view_func.__dict__
        _filter.__doc__  = view_func.__doc__

        return _filter

    if function is None:
        return _dec
    else:
        return _dec(function)


class Marionet(Portlet):
    """A simple portlet to display some text.
    """
    VERSION = '0.0.1'

    name   = u"help"
    url    = models.TextField(u"url",    blank=True)
    params = models.TextField(u"params", blank=True)

    def __unicode__(self):
        return "%s" % self.name

    def __init__(self):
        log.info("Marionet %s version %s" % (self.name,self.VERSION))
        self.config = Config()

    @portlet_filter
    def render(self, context=None):
        """
        """
        log.debug("View "+self.name)
        return ""

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
