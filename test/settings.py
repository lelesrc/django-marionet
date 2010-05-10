# -*- coding: utf-8 -*-
"""
For a given Django application, the test runner looks for
unit tests in two places:

    * The ``models.py`` file. The test runner looks for any subclass of
      ``unittest.TestCase`` in this module.

    * A file called ``tests.py`` in the application directory -- i.e., the
      directory that holds ``models.py``. Again, the test runner looks for any
      subclass of ``unittest.TestCase`` in this module.
"""
import os
import django.conf.global_settings as DEFAULT_SETTINGS

DEBUG = True
TEMPLATE_DEBUG = DEBUG

import logging
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
    filename = 'marionet.log',
    filemode = 'w'
)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

DATABASES = {
    'default': {
        'ENGINE':    'django.db.backends.sqlite3',
        'NAME':      'maindb',
        'TEST_NAME': 'testdb',
    }
}
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'portlets',
    'portlets.example',
    'marionet',
)
ROOT_URLCONF = 'test.portal.urls'
TEMPLATE_DIRS = (
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'marionet', 'templates'),
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'portal', 'templates'),
    )
SITE_ID = 1
TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'marionet.context_processors.render_ctx',
)

