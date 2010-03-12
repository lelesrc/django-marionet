test: syncdb
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py test marionet

syncdb:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py syncdb

runserver: syncdb
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py runserver

portlets:
	-mkdir vendor
	if [ -e vendor/django-portlets ]; then \
		cd vendor/django-portlets && hg pull ;\
	else \
		cd vendor && hg clone https://lamikae@bitbucket.org/lamikae/django-portlets/ ;\
		ln -s vendor/django-portlets/portlets . ;\
	fi

.PHONY: test syncdb runserver portlets
