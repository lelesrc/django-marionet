# -*- coding: utf-8 -*-
#
# TextPortlet copied from django-portlets (BSD license)
# author: diefenbach
#

# django imports
from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log, Config

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

    def __call__(self,func):
        """
        Filter.
        Prepares the state of the Marionet object.
        """
        log.debug("Filter activated")
        return func

    def render(self, context=None):
        """Renders the portlet as html.
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
