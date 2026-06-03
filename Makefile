IMAGE_NAME := kosli-demo/$(notdir $(CURDIR))
export DOCKER_CLI_HINTS=false

.PHONY: image demo

image:
	docker build --tag $(IMAGE_NAME) .

demo: image
	docker compose up --detach --wait
	@curl --silent http://localhost:5001/repo-name | jq .
	@curl --silent http://localhost:5001/timestamp | jq .
	docker compose down
