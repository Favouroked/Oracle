#!/bin/bash

# Oracle AI Global Installation Script
# This script installs Oracle AI into a dedicated virtual environment
# and creates a symlink in /usr/local/bin to make it available system-wide.

set -e

# Configuration
INSTALL_DIR="$HOME/.oracle-ai"
PYTHON_CMD="python3"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find a suitable binary directory
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    SYMLINK_DIR="$HOME/.local/bin"
else
    SYMLINK_DIR="/usr/local/bin"
fi
SYMLINK_PATH="$SYMLINK_DIR/oracle"

echo "========================================"
echo "    Oracle AI Global Installation"
echo "========================================"

# Check for Python version
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: $PYTHON_CMD not found. Please install Python 3.13 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 13 ]); then
    echo "Error: Oracle requires Python 3.13 or higher. Found Python $PYTHON_VERSION."
    exit 1
fi

echo "Found Python $PYTHON_VERSION."

# Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "WARNING: Ollama is not installed."
    echo "Oracle requires Ollama to run LLM inference locally."
    read -p "Would you like to install Ollama now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "Skipping Ollama installation."
        echo "Please install Ollama manually from: https://ollama.com/download"
    fi
else
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    echo "Found Ollama: $OLLAMA_VERSION"
fi

# Create installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo "Existing installation found at $INSTALL_DIR. Updating..."
else
    echo "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Create/Update virtual environment
echo "Setting up virtual environment..."
$PYTHON_CMD -m venv "$INSTALL_DIR/venv"

# Install/Update Oracle
echo "Installing Oracle package..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install "$SCRIPT_DIR"

# Create symlink in /usr/local/bin
echo "Creating system-wide symlink at $SYMLINK_PATH..."
if [ -w "$(dirname $SYMLINK_PATH)" ]; then
    ln -sf "$INSTALL_DIR/venv/bin/oracle" "$SYMLINK_PATH"
else
    echo "Requesting sudo permissions to create symlink..."
    sudo ln -sf "$INSTALL_DIR/venv/bin/oracle" "$SYMLINK_PATH"
fi

echo "----------------------------------------"
echo "Success! Oracle AI has been installed."
echo "You can now run 'oracle' from any terminal."
echo "To uninstall, run: oracle uninstall"
echo "========================================"

# Check if default model is available and offer to pull if not
if command -v ollama &> /dev/null; then
    DEFAULT_MODEL="qwen3.5:4b"
    if ollama list 2>/dev/null | grep -q "^$DEFAULT_MODEL"; then
        echo "Default model '$DEFAULT_MODEL' is already available."
    else
        echo ""
        read -p "Default model '$DEFAULT_MODEL' not found. Would you like to pull it now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Pulling $DEFAULT_MODEL model (this may take a while)..."
            ollama pull $DEFAULT_MODEL
        else
            echo "Skipping model download. You can pull it later with: ollama pull $DEFAULT_MODEL"
        fi
    fi
fi
