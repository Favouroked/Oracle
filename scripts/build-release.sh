# scripts/build-release.sh
#!/bin/bash
set -e

VERSION="${1:-$(grep 'version' pyproject.toml | head -1 | cut -d'"' -f2)}"
RELEASE_NAME="oracle-$VERSION"

echo "Building release: $RELEASE_NAME"

# Clean previous builds
rm -rf dist/ "$RELEASE_NAME" "$RELEASE_NAME.tar.gz" "$RELEASE_NAME.zip"

# Create release directory
mkdir -p "$RELEASE_NAME"
cp -r oracle install.sh pyproject.toml README.md LICENSE "$RELEASE_NAME/"

# Create archives
tar -czvf "$RELEASE_NAME.tar.gz" "$RELEASE_NAME"
zip -r "$RELEASE_NAME.zip" "$RELEASE_NAME"

# Cleanup
rm -rf "$RELEASE_NAME"

echo "✅ Created: $RELEASE_NAME.tar.gz and $RELEASE_NAME.zip"