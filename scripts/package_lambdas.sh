#!/usr/bin/env bash
# Package Lambda functions with dependencies for deployment.
# Produces: backend/build/backend.zip, infrastructure/build/layer.zip
# Run from repo root: ./scripts/package_lambdas.sh
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
INFRA_DIR="$REPO_ROOT/infrastructure"
BACKEND_BUILD="$BACKEND_DIR/build"
INFRA_BUILD="$INFRA_DIR/build"

echo "==> Packaging backend source (from $BACKEND_DIR)..."
mkdir -p "$BACKEND_BUILD"
rm -f "$BACKEND_BUILD/backend.zip"
(cd "$BACKEND_DIR" && zip -rq "$BACKEND_BUILD/backend.zip" . \
  -x "*.pyc" -x "*__pycache__*" -x "build/*" -x "*.zip" \
  -x "tests/*" -x ".venv/*" -x "venv/*" -x ".env*" \
  -x "*.egg-info/*" -x ".pytest_cache/*" -x "*.md" \
  -x "schema/*" -x "migrations/*" -x "scripts/*")
echo "    Created $BACKEND_BUILD/backend.zip ($(du -h "$BACKEND_BUILD/backend.zip" | cut -f1))"

echo "==> Building dependency layer (psycopg2)..."
mkdir -p "$INFRA_BUILD/layer/python"
pip install --target "$INFRA_BUILD/layer/python" psycopg2-binary -q 2>/dev/null || true
(cd "$INFRA_BUILD/layer" && zip -rq "$INFRA_BUILD/layer.zip" .)
echo "    Created $INFRA_BUILD/layer.zip ($(du -h "$INFRA_BUILD/layer.zip" | cut -f1))"

echo "==> Package complete. Run ./scripts/deploy.sh to deploy via Terraform."
