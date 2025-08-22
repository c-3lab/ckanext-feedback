#!/bin/bash
set -e

# Project root directory (location of pyproject.toml)
PROJECT_ROOT="/srv/app/src_extensions/ckanext-feedback"

# site-packages side (test target code)
SITE_PACKAGES="/usr/lib/python3.10/site-packages/ckanext/feedback/tests"

cd "$PROJECT_ROOT"

# Environment variable settings
export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
export CKAN_SQLALCHEMY_URL=
export CKAN_DATASTORE_READ_URL=
export CKAN_DATASTORE_WRITE_URL=

# Run pytest from the project root (read pyproject.toml)
pytest --rootdir="$PROJECT_ROOT" "$@"
