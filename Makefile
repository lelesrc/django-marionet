test:
	PYTHONPATH=`pwd`:../django-portlets DJANGO_SETTINGS_MODULE=settings python test/test_helper.py 

.PHONY: test
