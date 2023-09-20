#!/bin/bash -e
# Clone CKAN and checkout ckan-2.9.7
git submodule update --init --recursive
# Copy docker/.env.template as .env
cp external/ckan/contrib/docker/.env.template external/ckan/contrib/docker/.env
# overwrite the version of zopw.interface from 4.3.2 to 5.0.0
sed -i -e 's/zope.interface==4.3.2/zope.interface==5.0.0/' external/ckan/requirements.txt
# Build and compose docker containers
docker compose -f external/ckan/contrib/docker/docker-compose.yml -f docker-compose.yml up --build -d