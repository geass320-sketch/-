#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
ZIP_NAME="storyboard-app.zip"

mkdir -p "$DIST_DIR"

cp "$ROOT_DIR/index.html" "$DIST_DIR/"
cp "$ROOT_DIR/styles.css" "$DIST_DIR/"
cp "$ROOT_DIR/app.js" "$DIST_DIR/"

(
  cd "$DIST_DIR"
  zip -r -q "$ZIP_NAME" index.html styles.css app.js
)

echo "Package created at $DIST_DIR/$ZIP_NAME"
