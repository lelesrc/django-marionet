# -*- coding: utf-8 -*-
#

from django import template

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log

register = template.Library()

@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet(context,portlet):
    """
    """
    log.debug("rendering context: %s" % (context))
    return {
        'portlet': context['portlet']
    }
