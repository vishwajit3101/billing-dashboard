#!/usr/bin/env bash
# Full deployment: package Lambdas, upload (optional), Terraform apply, run DB migrations.
# Run from repo root: ./scripts/deploy.sh [plan|apply]
# Requires: terraform, aws cli, psql (for migrations). Set TF_VAR_alert_email (or use tfvars).
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
INFRA_DIR="$REPO_ROOT/infrastructure"
ACTION="${1:-apply}"

echo "==> Step 1: Package Lambda functions..."
"$REPO_ROOT/scripts/package_lambdas.sh"

echo "==> Step 2: (Optional) Upload to S3..."
if [ -n "${LAMBDA_S3_BUCKET:-}" ]; then
  aws s3 cp "$BACKEND_DIR/build/backend.zip" "s3://$LAMBDA_S3_BUCKET/billing-watch/backend.zip" --quiet 2>/dev/null || true
  aws s3 cp "$INFRA_DIR/build/layer.zip" "s3://$LAMBDA_S3_BUCKET/billing-watch/layer.zip" --quiet 2>/dev/null || true
  echo "    Uploaded to s3://$LAMBDA_S3_BUCKET/billing-watch/"
else
  echo "    Set LAMBDA_S3_BUCKET to upload artifacts to S3 (Terraform can use them)."
fi

echo "==> Step 3: Terraform $ACTION..."
cd "$INFRA_DIR"
if [ "$ACTION" = "plan" ]; then
  terraform plan -out=tfplan
  echo "Run 'terraform apply tfplan' to apply."
  exit 0
fi
terraform apply -auto-approve

echo "==> Step 4: Run database migrations..."
# Get RDS endpoint and secret ARN from Terraform output
RDS_ENDPOINT="$(terraform output -raw rds_endpoint 2>/dev/null)" || true
DB_SECRET_ARN="$(terraform output -raw db_secret_arn 2>/dev/null)" || true
if [ -z "$RDS_ENDPOINT" ] || [ -z "$DB_SECRET_ARN" ]; then
  echo "    Skipping migrations (no rds_endpoint or db_secret_arn). Run manually:"
  echo "    aws secretsmanager get-secret-value --secret-id <db_secret_arn> --query SecretString --output text"
  echo "    psql \"postgresql://USER:PASSWORD@<rds_endpoint>:5432/billing_watch\" -f backend/schema/init_db.sql"
  exit 0
fi
# Fetch DB credentials from Secrets Manager and run init_db.sql
SECRET_JSON="$(aws secretsmanager get-secret-value --secret-id "$DB_SECRET_ARN" --query SecretString --output text 2>/dev/null)" || true
if [ -z "$SECRET_JSON" ]; then
  echo "    Could not fetch DB secret. Run migrations manually (see above)."
  exit 0
fi
DB_USER="$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('username','postgres'))")"
DB_PASS="$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('password',''))")"
DB_NAME="$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('dbname','billing_watch'))")"
export PGPASSWORD="$DB_PASS"
if command -v psql >/dev/null 2>&1; then
  echo "    Running init_db.sql..."
  psql -h "$RDS_ENDPOINT" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f "$BACKEND_DIR/schema/init_db.sql" || true
  if [ -f "$BACKEND_DIR/schema/002_exhaustion_predictions.sql" ]; then
    psql -h "$RDS_ENDPOINT" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f "$BACKEND_DIR/schema/002_exhaustion_predictions.sql" || true
  fi
  echo "    Migrations complete."
else
  echo "    psql not found. Run migrations manually (see above)."
fi
unset PGPASSWORD

echo "==> Deployment finished."
echo "    API URL: $(cd "$INFRA_DIR" && terraform output -raw api_base_url 2>/dev/null || echo 'N/A')"
