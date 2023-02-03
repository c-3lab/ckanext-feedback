#!/bin/bash -e
# Clone CKAN and checkout ckan-2.9.7
git submodule update --init --recursive
# Copy docker/.env.template as .env
cp external/ckan/contrib/docker/.env.template external/ckan/contrib/docker/.env
# Build and compose docker containers
docker compose -f external/ckan/contrib/docker/docker-compose.yml -f docker-compose.yml up --build -d
# Copy cli.py and create.py to the CKAN container ckan/cli/ folder
docker cp misc/cli.py ckan:/usr/lib/ckan/venv/src/ckan/ckan/cli/cli.py
docker cp misc/create.py ckan:/usr/lib/ckan/venv/src/ckan/ckan/cli/create.py
