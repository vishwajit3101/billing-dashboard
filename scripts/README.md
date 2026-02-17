# Billing Watch — Scripts

## package_lambdas.sh

Packages backend and dependency layer for Lambda deployment.

- **Output:** `backend/build/backend.zip`, `infrastructure/build/layer.zip`
- **Run from repo root:** `./scripts/package_lambdas.sh` (or `bash scripts/package_lambdas.sh`)

Requires: `zip`, `pip`, Python 3.11+.

## deploy.sh

Full deployment: package → (optional S3 upload) → Terraform apply → DB migrations.

- **Run from repo root:** `./scripts/deploy.sh [plan|apply]`
- **Default:** `apply`. Use `plan` to only run `terraform plan`.
- **Env (optional):**
  - `LAMBDA_S3_BUCKET` — if set, uploads `backend.zip` and `layer.zip` to `s3://$LAMBDA_S3_BUCKET/billing-watch/`
  - `TF_VAR_alert_email` or use `terraform.tfvars` for `alert_email`
- **Migrations:** After Terraform, the script fetches RDS endpoint and DB secret from Terraform output and runs `backend/schema/init_db.sql` (and `002_exhaustion_predictions.sql` if present) via `psql`. Requires `psql` and AWS CLI if you want automatic migrations.

## Tests

Run the backend test suite from the backend directory:

```bash
cd backend
pip install -r requirements.txt   # includes pytest, psycopg2-binary
python -m pytest tests/ -v
python -m pytest tests/ --cov=src --cov=lambda_functions --cov-report=term-missing  # with coverage
```

See `backend/tests/` and `backend/pytest.ini`.
