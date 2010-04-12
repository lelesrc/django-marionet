# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from test.settings import MEDIA_ROOT
urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^demo',    'test.portal.views.marionet'),
    (r'^hack',    'test.portal.views.ajax_generator'),
    (r'^jquery',  'test.portal.views.jquery_test'),
    (r'^portal/', 'test.portal.views.index'),

    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
)

