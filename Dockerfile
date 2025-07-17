# Use an official Python runtime as a parent image
# The Python version can be specified at build time with --build-arg PYTHON_VERSION=3.9
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Install system dependencies:
# - git: for version control
# - curl, gpg, apt-transport-https: for adding github-cli repository
# - gnupg, software-properties-common: for managing repositories
# - procps: provides 'ps' command, useful for debugging
# - nodejs & npm: for installing claude-code
# - curl: is also needed to install uv
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
# The installation script places it in /root/.local/bin, so we add it to the PATH.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install the GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh -y

# Install claude-code globally using npm
RUN npm install -g @anthropic-ai/claude-code

COPY commands .claude/commands
# Default command to keep the container running in the background.
# You can get an interactive shell by using 'docker exec'.
CMD ["tail", "-f", "/dev/null"]
