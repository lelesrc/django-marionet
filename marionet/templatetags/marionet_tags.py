# -*- coding: utf-8 -*-
#

from django import template

from portlets.models import Portlet
from portlets.utils import register_portlet

from marionet.models import PortletUrl
from marionet import log
from test.settings import TEST_LOG_LEVEL
log.setlevel(TEST_LOG_LEVEL)

register = template.Library()

@register.inclusion_tag('marionet/portlet.html', takes_context=True)
def marionet(context,portlet):
    """
    """
    log.debug("rendering context: %s" % (context))
    return {
        'portlet': portlet.render(context),
        'title': portlet.url
    }
