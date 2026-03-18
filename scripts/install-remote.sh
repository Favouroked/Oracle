# scripts/install-remote.sh
#!/bin/bash

# Oracle AI Remote Installation Script
# Usage: curl -fsSL https://raw.githubusercontent.com/Favouroked/Oracle/main/scripts/install-remote.sh | bash

set -e

REPO="Favouroked/oracle"  # <- Update this with your GitHub username
INSTALL_DIR="$HOME/.oracle-ai"

echo "========================================"
echo "    Oracle AI Remote Installer"
echo "========================================"

# Cleanup function
cleanup() {
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
    fi
}
trap cleanup EXIT

# Detect latest release or fall back to main branch
echo "Fetching latest release..."
LATEST_TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | grep '"tag_name"' | cut -d'"' -f4 || echo "")

if [ -n "$LATEST_TAG" ]; then
    echo "Found release: $LATEST_TAG"
    DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST_TAG/oracle-$LATEST_TAG.tar.gz"
else
    echo "No releases found, using main branch..."
    DOWNLOAD_URL="https://github.com/$REPO/archive/refs/heads/main.tar.gz"
    LATEST_TAG="main"
fi

# Create temporary directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download and extract
echo "Downloading Oracle..."
if ! curl -fsSL "$DOWNLOAD_URL" -o oracle.tar.gz; then
    echo "Error: Failed to download Oracle. Check your internet connection."
    exit 1
fi

echo "Extracting..."
tar -xzf oracle.tar.gz
rm oracle.tar.gz

# Find the extracted directory (handles both release and main branch naming)
EXTRACTED_DIR=$(ls -d */ | head -1)
cd "$EXTRACTED_DIR"

# Run the install script
echo "Running installer..."
if [ -f "install.sh" ]; then
    chmod +x install.sh
    ./install.sh
else
    echo "Error: install.sh not found in the downloaded archive."
    exit 1
fi

echo ""
echo "🎉 Installation complete!"
echo "Run 'oracle --help' to get started."