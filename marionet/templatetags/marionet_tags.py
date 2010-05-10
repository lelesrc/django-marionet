# -*- coding: utf-8 -*-
#

import logging

from django import template

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet.models import Marionet

register = template.Library()

# until django integrates http://code.djangoproject.com/ticket/12772
# namespace is prefixed to tag name 

@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet_render(context,portlet):
    """ Portlet with funny CSS.
    """
    logging.debug(" % % % render tag")
    content = portlet.render(context)
    title = portlet.title
    logging.debug("rendering portlet: %s" % (portlet))
    return {
        'title': title,
        'content': content,
    }

'''
@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet_portletRequest(context,url):
    """ 
    """
    #logging.debug("marionet context: %s" % (context))
    logging.debug("request new url")
    logging.debug(url)
    return {}
    """
    portlet = Marionet(url=url)
    logging.debug("marionet portlet: %s" % (portlet))
    return {
        'portlet': portlet
    }
    """
'''