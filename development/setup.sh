#!/bin/bash
git clone https://github.com/ckan/ckan external/ckan
git submodule update --init --recursive
cd external/ckan
git checkout ckan-2.9.7
cd ../../
cp external/ckan/contrib/docker/.env.template external/ckan/contrib/docker/.env
docker compose -f external/ckan/contrib/docker/docker-compose.yml -f misc/docker-compose.yml up --build -d
