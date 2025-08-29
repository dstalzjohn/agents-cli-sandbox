#!/bin/bash
# Docker/Podman setup and verification script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🐳 Docker/Podman Setup Verification"
echo "===================================="

# Check for Docker or Podman
if command -v docker &> /dev/null; then
    RUNTIME="docker"
    RUNTIME_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker found: $RUNTIME_VERSION"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
    RUNTIME_VERSION=$(podman --version)
    echo -e "${GREEN}✓${NC} Podman found: $RUNTIME_VERSION"
else
    echo -e "${RED}✗${NC} Neither Docker nor Podman is installed!"
    echo "Please install Docker or Podman to continue."
    echo ""
    echo "Installation instructions:"
    echo "  Docker: https://docs.docker.com/get-docker/"
    echo "  Podman: https://podman.io/getting-started/installation"
    exit 1
fi

# Check if runtime is running
if [ "$RUNTIME" = "docker" ]; then
    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} Docker daemon is not running!"
        echo "Please start Docker and try again."
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Docker daemon is running"
fi

# Check for docker-compose (optional)
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose found: $COMPOSE_VERSION"
elif $RUNTIME compose version &> /dev/null; then
    COMPOSE_VERSION=$($RUNTIME compose version)
    echo -e "${GREEN}✓${NC} $RUNTIME compose found: $COMPOSE_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Docker Compose not found (optional)"
fi

# Check for .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Environment file .env found"
else
    echo -e "${YELLOW}⚠${NC} No .env file found"
    echo "Creating .env from sample.env..."
    if [ -f "sample.env" ]; then
        cp sample.env .env
        echo -e "${GREEN}✓${NC} Created .env from sample.env"
        echo "Please edit .env to set your configuration values"
    else
        echo -e "${RED}✗${NC} sample.env not found!"
    fi
fi

echo ""
echo "Setup verification complete!"
echo ""
echo "Available commands:"
echo "  make build       - Build the container image"
echo "  make run         - Run the container"
echo "  make shell       - Connect to container shell"
echo "  make stop        - Stop the container"
echo "  make remove      - Remove the container"
echo "  make compose-up  - Start with docker-compose (if available)"
echo "  make info        - Show runtime information"

# Show current runtime for Makefile
echo ""
echo "Runtime that will be used: $RUNTIME"