SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

.PHONY: lock build verify scan unit ci help

lock:  ## Resolve exact signed package locks for both variants.
	./scripts/resolve-locks.sh

build: lock  ## Build and load the runtime and build images.
	./scripts/build-images.sh

verify:  ## Verify the already-built image contracts.
	./scripts/verify-images.sh

scan:  ## Report findings and apply the fleet vulnerability gate.
	./scripts/scan-images.sh

unit:  ## Run policy and lock mutation tests without Docker.
	python3 -m unittest discover -s tests/unit -p 'test_*.py' -v

ci: unit build verify scan  ## Run the complete local validation path.

help:  ## Show available targets.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'
