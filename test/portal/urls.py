# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^demo',    'test.portal.views.text_portlet'),
    (r'^hack',    'test.portal.views.marionet'),
    (r'^portal/', 'test.portal.views.index'),

)

