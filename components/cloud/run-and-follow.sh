#!/bin/bash

set -e
docker-compose build
docker-compose up -d -t 1 --force-recreate
docker-compose logs -f -t --tail=500
