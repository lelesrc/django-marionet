test:
	PYTHONPATH=`pwd`:`pwd`/../django-portlets DJANGO_SETTINGS_MODULE=test.settings django-admin.py test

.PHONY: test
