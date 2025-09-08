# Makefile for managing the development container

# --- Variables ---
# Define the image and container names as variables for easy changes.
IMAGE_NAME := dev-client-env
CONTAINER_NAME := my-dev-client

# Detect container runtime (Docker or Podman)
CONTAINER_RUNTIME := $(shell command -v docker 2> /dev/null || command -v podman 2> /dev/null)
ifeq ($(CONTAINER_RUNTIME),)
    $(error Neither Docker nor Podman is installed. Please install one of them.)
endif

# Extract just the command name (docker or podman)
RUNTIME_NAME := $(notdir $(CONTAINER_RUNTIME))

# --- Environment File ---
# Check if a .env file exists and include it. This makes variables available to the shell.
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# --- Targets ---

# Build the container image using the Dockerfile in the current directory.
# Use: make build
build:
	@echo "Building container image: $(IMAGE_NAME) using $(RUNTIME_NAME)..."
	@$(CONTAINER_RUNTIME) build --build-arg REPO_URL=$(REPO_URL) -t $(IMAGE_NAME) .

# Run the container in detached mode.
# This command now uses the --env-file flag to pass all variables from .env directly.
# Use: make run
run:
	@echo "Running container: $(CONTAINER_NAME) using $(RUNTIME_NAME)..."
	@if [ -f .env ]; then \
		$(CONTAINER_RUNTIME) run \
		  --env-file .env \
		  -d --name $(CONTAINER_NAME) $(IMAGE_NAME); \
	else \
		$(CONTAINER_RUNTIME) run \
		  -d --name $(CONTAINER_NAME) $(IMAGE_NAME); \
	fi

# Stop the container by its name.
# Use: make stop
stop:
	@echo "Stopping container: $(CONTAINER_NAME) using $(RUNTIME_NAME)..."
	@$(CONTAINER_RUNTIME) stop $(CONTAINER_NAME) || true

# Remove the container by its name.
# Use: make remove
remove:
	@echo "Removing container: $(CONTAINER_NAME) using $(RUNTIME_NAME)..."
	@$(CONTAINER_RUNTIME) rm $(CONTAINER_NAME) || true

# Stop and remove the container by its name.
# Use: make stop_and_remove
stop_and_remove: stop remove

# Start a stopped container without rebuilding.
# Use: make start
start:
	@echo "Starting container: $(CONTAINER_NAME) using $(RUNTIME_NAME)..."
	@$(CONTAINER_RUNTIME) start $(CONTAINER_NAME)

# A helper target to get an interactive shell inside the running container.
# Use: make shell
shell:
	@echo "Connecting to shell in container: $(CONTAINER_NAME) using $(RUNTIME_NAME)..."
	@$(CONTAINER_RUNTIME) exec -it $(CONTAINER_NAME) /bin/bash

# Check container logs
# Use: make logs
logs:
	@echo "Showing logs for container: $(CONTAINER_NAME)..."
	@$(CONTAINER_RUNTIME) logs $(CONTAINER_NAME)

# Build and run using docker-compose (if available)
# Use: make compose-up
compose-up:
	@if command -v docker-compose >/dev/null 2>&1; then \
		echo "Starting services with docker-compose..."; \
		docker-compose up -d; \
	elif $(CONTAINER_RUNTIME) compose version >/dev/null 2>&1; then \
		echo "Starting services with $(RUNTIME_NAME) compose..."; \
		$(CONTAINER_RUNTIME) compose up -d; \
	else \
		echo "Docker Compose not available, using standard build and run..."; \
		$(MAKE) build && $(MAKE) run; \
	fi

# Stop services using docker-compose (if available)
# Use: make compose-down
compose-down:
	@if command -v docker-compose >/dev/null 2>&1; then \
		echo "Stopping services with docker-compose..."; \
		docker-compose down; \
	elif $(CONTAINER_RUNTIME) compose version >/dev/null 2>&1; then \
		echo "Stopping services with $(RUNTIME_NAME) compose..."; \
		$(CONTAINER_RUNTIME) compose down; \
	else \
		echo "Docker Compose not available, using standard stop and remove..."; \
		$(MAKE) stop_and_remove; \
	fi

# Show runtime info
# Use: make info
info:
	@echo "Container Runtime: $(RUNTIME_NAME)"
	@echo "Runtime Path: $(CONTAINER_RUNTIME)"
	@echo "Image Name: $(IMAGE_NAME)"
	@echo "Container Name: $(CONTAINER_NAME)"
	@if [ -f .env ]; then \
		echo "Environment file: .env (found)"; \
	else \
		echo "Environment file: .env (not found - using defaults)"; \
	fi

.PHONY: build run stop remove stop_and_remove start shell logs compose-up compose-down info
