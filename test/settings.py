"""
For a given Django application, the test runner looks for
unit tests in two places:

    * The ``models.py`` file. The test runner looks for any subclass of
      ``unittest.TestCase`` in this module.

    * A file called ``tests.py`` in the application directory -- i.e., the
      directory that holds ``models.py``. Again, the test runner looks for any
      subclass of ``unittest.TestCase`` in this module.
"""

DEBUG = False
#TEMPLATE_DIRS = ('')
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
    'marionet',
)
