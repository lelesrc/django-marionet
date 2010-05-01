# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from test.settings import MEDIA_ROOT
urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    (r'^portal/', 'test.portal.views.index'),

    (r'^test_bench/xhr', 'test.portal.views.test_bench_xhr'),
    (r'^test_bench/', 'test.portal.views.test_bench'),

    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
)

