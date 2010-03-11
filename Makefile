test: syncdb
	PYTHONPATH=`pwd`:`pwd`/../django-portlets DJANGO_SETTINGS_MODULE=test.settings django-admin.py test

syncdb:
	PYTHONPATH=`pwd`:`pwd`/../django-portlets DJANGO_SETTINGS_MODULE=test.settings django-admin.py syncdb

runserver: syncdb
	PYTHONPATH=`pwd`:`pwd`/../django-portlets DJANGO_SETTINGS_MODULE=test.settings django-admin.py runserver


.PHONY: test
