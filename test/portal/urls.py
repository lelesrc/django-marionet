# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^portal/site', 'test.portal.views.site'),
    (r'^portal/', 'test.portal.views.index'),
#    (r'^admin/', include(admin.site.urls)),

)

