REPO := cpnet/authdemo
VERSION := develop
IS_RELEASED := false
VER != jq -r '.version' api-fastify/package.json

image-fastify:
	docker buildx rm tfapp || true
	docker buildx create --platform linux/amd64 --name tfapp --use
	docker buildx build -t ${REPO}:${VERSION} --build-arg is_released=${IS_RELEASED} --load -f Dockerfile.fastify .
	docker buildx rm tfapp

image-fastapi:
	docker buildx rm tfapp || true
	docker buildx create --platform linux/amd64 --name tfapp --use
	docker buildx build -t ${REPO}:${VERSION} --load -f Dockerfile.fastapi .
	docker buildx rm tfapp


.PHONY: image-fastify image-fastapi
