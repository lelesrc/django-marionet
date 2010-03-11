# -*- coding: utf-8 -*-

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


#def index(request, obj, template_name="lfc/portal.html"):
def index(request):
    """Displays the the portal.
    """
    #return render_to_response(template_name, RequestContext(request, {    }))
    return HttpResponse("all ok :)")

def site(request):
    return render_to_response('site.html')
