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

DEBUG = True
TEST_LOG_LEVEL = 'critical'
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
TEMPLATE_DIRS = ('test/portal/templates')
SITE_ID = 1

