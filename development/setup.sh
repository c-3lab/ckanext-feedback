#!/bin/bash
git clone https://github.com/ckan/ckan external/ckan
git submodule update --init --recursive
cd external/ckan
git checkout ckan-2.9.7
cd ../../
cp external/ckan/contrib/docker/.env.template misc/.env
docker compose -f misc/docker-compose.yml up --build -d
