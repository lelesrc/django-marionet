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

from marionet.models import Marionet

def index(request):
    return HttpResponse("hello world")

def marionet(request):
    portlet_1 = Marionet.objects.create(title="....",url="",req_method="")
    portlet_2 = Marionet.objects.create(title="....",url="",req_method="")
    portlet_1.title="portlet 1"
    portlet_2.title="portlet 2"
    portlets = [portlet_1, portlet_2]
    return render_to_response("test_bench.html", {
        "portlets" : portlets,
        })
