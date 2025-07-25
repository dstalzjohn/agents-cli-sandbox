# Use an official Python runtime as a parent image
# The Python version can be specified at build time with --build-arg PYTHON_VERSION=3.9
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gpg \
    apt-transport-https \
    gnupg \
    software-properties-common \
    procps \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv (a fast Python package installer and resolver)
# This is installed as root, we will adjust the PATH for the non-root user later
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh -y

# Install claude-code globally using npm
RUN npm install -g @anthropic-ai/claude-code

# --- Create a non-root user to avoid permission issues ---
# Create a group and user first
RUN groupadd --gid 1000 devgroup && \
    useradd --uid 1000 --gid devgroup --shell /bin/bash --create-home devuser

# Copy your custom commands to the correct user's home directory
# and set ownership at the same time. This is the correct location.
COPY --chown=devuser:devgroup commands /home/devuser/.claude/commands
COPY --chown=devuser:devgroup claude-settings/settings.json /home/devuser/.claude/settings.jsonmak

# Give the new user ownership of the app directory
RUN chown -R devuser:devgroup /usr/src/app

# Switch to the non-root user
USER devuser

# Update PATH for the new user to find uv and other user-installed packages
ENV PATH="/home/devuser/.local/bin:/root/.local/bin:${PATH}"

# Copy the source code and Claude configuration
COPY --chown=devuser:devgroup src/ /usr/src/app/src/
COPY --chown=devuser:devgroup CLAUDE.md /usr/src/app/

# Install the package using pip
RUN pip install -e src/

# Default command to keep the container running in the background.
CMD ["tail", "-f", "/dev/null"]