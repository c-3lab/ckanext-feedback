#!/bin/bash -e
# Clone CKAN and checkout ckan-2.10.4
git submodule update --init --recursive
# Copy docker/.env.template as .env
cp .env.dev external/ckan-docker/.env
# Build and compose docker containers
docker compose -f external/ckan-docker/docker-compose.dev.yml -f docker-compose.yml up --build -d