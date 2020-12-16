DC=docker-compose
FORMATTER=black
UNAME_S := $(shell uname -s)
ROI=00

.PHONY: help

help: ## *:･ﾟ✧*:･ﾟ✧ This help *:･ﾟ✧*:･ﾟ✧
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk ' \
			BEGIN {FS = ":.*?## "}; \
			{printf "\033[31;1;40m[ \033[36;1;40m%13s \033[31;1;40m]\033[0;32;1m  %s\033[0m\n", $$1, $$2} \
		'

-: ## <     Installation          >
###################################

import: ## Import database
	$(DC) up --build database-import


-: ## <     Running Services      >
###################################

start: dirs build start-db daemon ## Build, start and follow log
	$(DC) logs -f --tail=100

build: ## Build components
	$(DC) build

clean: stop ## Shutdown, and remove all data
	$(DC) down -v --remove-orphans

daemon: dirs build start-db start-reader start-processor ## Run all services in background

stop: ## Stop all services
	$(DC) stop


-: ## <     Development tools     >
###################################

test: dirs build start-db ## Run pytest
	$(DC) run -e PYTHONPATH="/code" -e YOLO5_WEIGHTS="/tmp/yolov5s.pt" --entrypoint "pytest -p no:cacheprovider" processor
	$(DC) run -e PYTHONPATH="/code" --entrypoint "pytest -p no:cacheprovider" reader

formatter: ## Start code formatter
	which ${FORMATTER} >/dev/null && \
		${FORMATTER} \
			./database \
			./reader \
			./processor

test-processor: dirs ## Test running processor (FG)
	$(DC) up --build processor

test-reader: dirs ## Test running reader (FG)
	ROI=$(ROI) $(DC) up --build reader

test-reporter: ## Test running reporter (FG)
	$(DC) up --build reporter


# Internal, unlisted

dirs:
	mkdir -p processor/crop_images processor/videos processor/masks processor/warps
	chmod 777 processor/crop_images processor/videos processor/masks processor/warps

start-db:
	$(DC) up --build database-init

start-processor:
	$(DC) up -d --build processor

start-reader:
	$(DC) up -d --build reader

start-warp-gen: build ## Start warp file generation
	$(DC) run -e PYTHONPATH="/code" --entrypoint "python3 -m processor.warp_generator" processor
