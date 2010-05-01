# -*- coding: utf-8 -*-
# Test portal views

# python imports
import sys
import traceback

# django imports
from django import template
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# portlets imports
from portlets.utils import get_registered_portlets
from portlets.utils import get_slots
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot

from marionet.models import Marionet, log

def index(request):
    return HttpResponse("hello world")


def test_bench(request):
    portlet =  Marionet.objects.create(
        url="http://localhost:3000/caterpillar/test_bench/",
        )
    log.debug(portlet)
    return render_to_response("url.html", {
        "portlet" : portlet,
        },
        context_instance=RequestContext(request))


def test_bench_xhr(request):
    """ Marionet XHR ping
    """
    '''
    if request.is_ajax():
        return HttpResponse("OK")
    else:
        return HttpResponse("FAIL", status=404)
    '''
    if not request.is_ajax():
        return HttpResponse("FAIL", status=404)

    portlet =  Marionet.objects.create(
        url="http://localhost:3000/caterpillar/test_bench/junit/xhr_post",
        )
    log.debug(portlet)
    return render_to_response("url.html", {
        "portlet" : portlet,
        },
        context_instance=RequestContext(request))
