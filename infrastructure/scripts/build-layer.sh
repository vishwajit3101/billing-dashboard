#!/usr/bin/env bash
# Build Lambda layer zip for psycopg2 (required for RDS).
# Run from infrastructure/: ./scripts/build-layer.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$INFRA_DIR/build"
LAYER_DIR="$BUILD_DIR/layer"
mkdir -p "$LAYER_DIR/python"
pip install --target "$LAYER_DIR/python" psycopg2-binary -q
(cd "$LAYER_DIR" && zip -rq "$BUILD_DIR/layer.zip" .)
echo "Created $BUILD_DIR/layer.zip"
