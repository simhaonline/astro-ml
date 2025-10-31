REGISTRY ?= ghcr.io/${GITHUB_REPOSITORY_OWNER}
IMAGE    := ${REGISTRY}/astro-ml
TAG      ?= $(shell git rev-parse --short HEAD)

.PHONY: build push deploy test infra

infra:
	terraform -chdir=terraform init
	terraform -chdir=terraform apply -auto-approve

build:
	docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .
push: build
	docker push ${IMAGE}:${TAG}
	docker push ${IMAGE}:latest

deploy: push
	helm upgrade --install astro-ml k8s/ \
	  --set image.tag=${TAG} \
	  --wait --timeout=5m

test:
	pytest tests -q

port-forward:
	kubectl port-forward svc/astro-ml 8888:8888
