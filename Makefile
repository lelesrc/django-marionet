test: syncdb
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py test marionet portlets

reset:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py reset marionet portlets

syncdb:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py syncdb

sql:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py sql marionet portlets

runserver: syncdb
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=test.settings django-admin.py runserver

portlets:
	-mkdir vendor
	if [ ! -e vendor/django-portlets ]; then \
		cd vendor && hg clone https://lamikae@bitbucket.org/lamikae/django-portlets/ ;\
	else \
		cd vendor/django-portlets && hg pull ;\
	fi
	if [ ! -e portlets ]; then ln -s vendor/django-portlets/portlets . ; fi



.PHONY: test syncdb runserver portlets
