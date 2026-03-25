#!/bin/bash -e
# Clone CKAN and checkout ckan-2.10.4
git submodule update --init --recursive
cd ./external/ckan-docker
git checkout a870d3a166441e5acbda57497144231e4dba02c0
cd ../../
# Copy docker/.env.template as .env
cp .env.dev external/ckan-docker/.env
# Build and compose docker containers
docker compose -f external/ckan-docker/docker-compose.dev.yml -f docker-compose.yml up --build -d