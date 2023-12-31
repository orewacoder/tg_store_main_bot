#! /usr/bin/env sh

# Exit in case of error
set -e

TLD=${TLD?Variable not set} \
DOMAIN=${DOMAIN?Variable not set} \
TRAEFIK_TAG=${TRAEFIK_TAG?Variable not set} \
STACK_NAME=${STACK_NAME?Variable not set} \
TAG=${TAG?Variable not set} \
docker compose \
-f docker-compose.yml \
config | sed "/published:/s/\"//g" | sed "/^name:/d" > ./docker-stack.yml

#docker-auto-labels ./docker-stack.yml

docker stack deploy -c docker-stack.yml --with-registry-auth "${STACK_NAME?Variable not set}"