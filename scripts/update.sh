#!/bin/bash
set -e

# Update script for the container
# This script pulls the latest changes from the repository and updates
# scripts, claude-settings, and commands in the container

echo "Starting update process..."

# Create temporary directory
TMP_DIR="/tmp/repo_update_$$"
echo "Creating temporary directory: $TMP_DIR"
mkdir -p "$TMP_DIR"

# Clone the repository to temp directory
echo "Cloning repository: $REPO_URL"
gh repo clone "$REPO_URL" "$TMP_DIR" -- --depth=1

# Define target locations
SCRIPTS_TARGET="/usr/src/app/scripts"
COMMANDS_TARGET="/home/devuser/.claude/commands"
SETTINGS_TARGET="/home/devuser/.claude/settings.json"

# Update scripts
if [ -d "$TMP_DIR/scripts" ]; then
    echo "Updating scripts..."
    cp -r "$TMP_DIR/scripts/"* "$SCRIPTS_TARGET/" 2>/dev/null || echo "No scripts to copy"
else
    echo "No scripts directory found in repository"
fi

# Update commands
if [ -d "$TMP_DIR/commands" ]; then
    echo "Updating commands..."
    cp -r "$TMP_DIR/commands/"* "$COMMANDS_TARGET/" 2>/dev/null || echo "No commands to copy"
else
    echo "No commands directory found in repository"
fi

# Update claude settings
if [ -f "$TMP_DIR/claude-settings/settings.json" ]; then
    echo "Updating claude settings..."
    cp "$TMP_DIR/claude-settings/settings.json" "$SETTINGS_TARGET"
else
    echo "No claude settings found in repository"
fi

# Clean up temporary directory
echo "Cleaning up temporary directory..."
rm -rf "$TMP_DIR"

echo "Update completed successfully!"