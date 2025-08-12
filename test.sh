#!/bin/bash
cd /usr/lib/python3.10/site-packages/ckanext/feedback
export PYTHONPATH=/usr/lib/python3.10/site-packages/ckanext/feedback
export CKAN_SQLALCHEMY_URL=
export CKAN_DATASTORE_READ_URL=
export CKAN_DATASTORE_WRITE_URL=
pytest --ckan-ini=/srv/app/src_extensions/ckanext-feedback/ckanext/feedback/tests/config/test.ini "$@"

