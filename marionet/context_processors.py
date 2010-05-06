# -*- coding: utf-8 -*-
#

# django imports
'''
from django import forms
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string

from portlets.models import Portlet
from portlets.utils import register_portlet
'''

from urlparse import urlparse, urlunparse, urlsplit, urlunsplit, urljoin, ParseResult
from cgi import parse_qs
from urllib import quote, unquote

from marionet import log

def render_ctx(request):
    log.debug(' - - - render context preprocessor')
    location = ParseResult(
        'http',
        '%s:%s' % (request.META['SERVER_NAME'], request.META['SERVER_PORT']),
        request.path,
        '',
        '', # request.META['QUERY_STRING'], # no query string here!
        ''
        )
    log.debug('location: '+urlunparse(location))
    query = request.GET
    log.debug('query: ' + str(query))
    post = request.POST
    log.debug('POST: '+str(post))
    
    return {
        'location': location, # ParseResult
        'query': query, # QueryDict
        'post': post # QueryDict
    }