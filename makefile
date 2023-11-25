deploy-all: build-api deploy-api

build-api:
	TAG=prod bash ./scripts/build.sh

deploy-api:
	TLD=b4.uz \
	DOMAIN=api.b4.uz \
	TRAEFIK_TAG=api.b4.uz \
	STACK_NAME=pgnbot \
	TAG=prod bash ./scripts/deploy.sh
	#docker service ls -q | xargs -n1 docker service update --force


deploy-traefik:
	docker network create --driver=overlay traefik-public
	export NODE_ID=$(docker info -f '{{.Swarm.NodeID}}')
	docker node update --label-add traefik-public.traefik-public-certificates=true $NODE_ID
	export EMAIL=admin@investor-bot.com
	export DOMAIN=traefik.investor-bot.com
	export USERNAME=pgnbot
	export PASSWORD=o2UPXV378X9M4g3yPiRB
	export HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)
	docker stack deploy -c traefik-config.yml traefik
