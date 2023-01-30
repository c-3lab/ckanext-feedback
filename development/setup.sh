#!/bin/bash
# Clone CKAN and checkout ckan-2.9.7
git clone https://github.com/ckan/ckan external/ckan
git submodule update --init --recursive
cd external/ckan
git checkout ckan-2.9.7
# Change directory back to the "development" folder
cd ../../
# Copy docker/.env.template as .env
cp external/ckan/contrib/docker/.env.template external/ckan/contrib/docker/.env
# Copy cli.py and create.py to the CKAN container ckan/cli/ folder
docker cp cli.py ckan:/usr/lib/ckan/venv/src/ckan/ckan/cli/cli.py
docker cp create.py ckan:/usr/lib/ckan/venv/src/ckan/ckan/cli/create.py
# Build and compose docker containers
docker compose -f external/ckan/contrib/docker/docker-compose.yml -f misc/docker-compose.yml up --build -d