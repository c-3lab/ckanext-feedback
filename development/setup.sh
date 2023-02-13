#!/bin/bash -e
# Clone CKAN and checkout ckan-2.9.7
git submodule update --init --recursive
# Copy docker/.env.template as .env
cp external/ckan/contrib/docker/.env.template external/ckan/contrib/docker/.env
# Build and compose docker containers
docker compose -f external/ckan/contrib/docker/docker-compose.yml -f docker-compose.yml up --build -d