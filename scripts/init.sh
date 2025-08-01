#!/bin/bash
set -e

echo "============================================"
echo "Container Initialization Script"
echo "============================================"
echo ""

# Check if running interactively
if [ ! -t 0 ]; then
    echo "Error: This script requires interactive input. Please run with 'docker exec -it' or similar."
    exit 1
fi

echo "This script will help you set up:"
echo "1. GitHub CLI authentication"
echo "2. Claude Code authentication"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo "============================================"
echo "1. GitHub CLI Setup"
echo "============================================"

# Check if gh is already authenticated
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI is already authenticated"
    gh auth status
    echo ""
    read -p "Re-authenticate? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping GitHub authentication..."
    else
        echo "Logging out first..."
        gh auth logout || true
        echo ""
        echo "Starting GitHub authentication..."
        gh auth login
    fi
else
    echo "Starting GitHub authentication..."
    echo "Please follow the prompts to authenticate with GitHub:"
    gh auth login
fi

echo ""
echo "============================================"
echo "2. Claude Code Setup"
echo "============================================"

# Check if claude is already authenticated
if claude auth whoami &>/dev/null; then
    echo "✅ Claude Code is already authenticated"
    claude auth whoami
    echo ""
    read -p "Re-authenticate? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping Claude authentication..."
    else
        echo "Starting Claude Code authentication..."
        claude auth login
    fi
else
    echo "Starting Claude Code authentication..."
    echo "Please follow the prompts to authenticate with Claude:"
    claude auth login
fi

echo ""
echo "============================================"
echo "Initialization Complete!"
echo "============================================"
echo ""
echo "✅ GitHub CLI: $(gh auth status --show-token 2>/dev/null | head -1 || echo 'Authenticated')"
echo "✅ Claude Code: $(claude auth whoami 2>/dev/null || echo 'Authenticated')"
echo ""
echo "You can now:"
echo "- Use 'gh' commands to interact with GitHub"
echo "- Use 'claude' commands for AI assistance"
echo "- Run './scripts/update.sh' to update container files"
echo ""
echo "Happy coding! 🚀"