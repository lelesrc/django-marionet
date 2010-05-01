# -*- coding: utf-8 -*-
#

from django import template

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet import log
from marionet.models import Marionet
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

register = template.Library()

# until django integrates http://code.djangoproject.com/ticket/12772
# namespace is prefixed to tag name 

@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet_render(context,portlet):
    """ Portlet with funny CSS.
    """
    log.debug(" % render tag")
    content = portlet.render(context)
    title = portlet.title
    log.debug("marionet portlet: %s" % (title))
    return {
        'title': title,
        'content': content,
    }

'''
@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet_portletRequest(context,url):
    """ 
    """
    #log.debug("marionet context: %s" % (context))
    log.debug("request new url")
    log.debug(url)
    return {}
    """
    portlet = Marionet(url=url)
    log.debug("marionet portlet: %s" % (portlet))
    return {
        'portlet': portlet
    }
    """
'''