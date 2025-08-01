# Makefile for managing the development container

# --- Variables ---
# Define the image and container names as variables for easy changes.
IMAGE_NAME := dev-client-env
CONTAINER_NAME := my-dev-client

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
	@echo "Building container image: $(IMAGE_NAME)..."
	@podman build --build-arg REPO_URL=$(REPO_URL) -t $(IMAGE_NAME) .

# Run the container in detached mode.
# This command now uses the --env-file flag to pass all variables from .env directly.
# Use: make run
run:
	@echo "Running container: $(CONTAINER_NAME)..."
	@podman run \
	  --env-file .env \
	  -d --name $(CONTAINER_NAME) $(IMAGE_NAME)

# Stop the container by its name.
# Use: make stop
stop:
	@echo "Stopping container: $(CONTAINER_NAME)..."
	@podman stop $(CONTAINER_NAME) || true

# Remove the container by its name.
# Use: make remove
remove:
	@echo "Removing container: $(CONTAINER_NAME)..."
	@podman rm $(CONTAINER_NAME) || true

# Stop and remove the container by its name.
# Use: make stop_and_remove
stop_and_remove: stop remove

# Start a stopped container without rebuilding.
# Use: make start
start:
	@echo "Starting container: $(CONTAINER_NAME)..."
	@podman start $(CONTAINER_NAME)

# A helper target to get an interactive shell inside the running container.
# Use: make shell
shell:
	@echo "Connecting to shell in container: $(CONTAINER_NAME)..."
	@podman exec -it $(CONTAINER_NAME) /bin/bash

.PHONY: build run stop remove stop_and_remove start shell
