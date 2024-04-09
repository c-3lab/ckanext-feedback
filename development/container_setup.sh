#!/bin/bash -e
# Clone CKAN and checkout ckan-2.10.4
git submodule update --init --recursive
cd ./external/ckan-docker
git checkout 89c900fe1c45565c6bb2723d99216ecf334ce44e
cd ../../
# Copy docker/.env.template as .env
cp .env.dev external/ckan-docker/.env
# Build and compose docker containers
docker compose -f external/ckan-docker/docker-compose.dev.yml -f docker-compose.yml up --build -d