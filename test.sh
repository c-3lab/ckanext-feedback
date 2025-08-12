#!/bin/bash
cd /srv/app/src_extensions/ckanext-feedback
export PYTHONPATH=/srv/app/src_extensions/ckanext-feedback
export CKAN_SQLALCHEMY_URL=
export CKAN_DATASTORE_READ_URL=
export CKAN_DATASTORE_WRITE_URL=
pytest "$@"
