# Billing Watch — Infrastructure (Terraform)

Deploys the full backend: VPC, RDS PostgreSQL, 5 Lambdas, API Gateway, EventBridge, Secrets Manager, SES.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured (or env vars `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`)
- Python 3.11+ and `pip` (for building the Lambda layer)

## Quick start

1. **Build the Lambda dependency layer** (psycopg2 for RDS):

   ```bash
   cd infrastructure
   ./scripts/build-layer.sh
   ```

2. **Create `terraform.tfvars`** (at least):

   ```hcl
   alert_email = "your-verified-email@example.com"
   # Optional: db_username = "postgres"
   # Optional: db_password = "..."  # leave empty to auto-generate
   ```

3. **Initialize and apply:**

   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **After RDS is up**, run the DB schema (from the machine that can reach RDS or via a bastion):

   ```bash
   psql "postgresql://USER:PASSWORD@$(terraform output -raw rds_endpoint):5432/billing_watch" -f ../backend/schema/init_db.sql
   ```

   Get the password from Secrets Manager or from the Terraform-generated value (if you didn’t set `db_password`).

## Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `environment` | Environment name | `dev` |
| `aws_region` | AWS region | `us-east-1` |
| `vpc_cidr` | VPC CIDR | `10.0.0.0/16` |
| `db_instance_class` | RDS instance class | `db.t3.micro` |
| `db_name` | Database name | `billing_watch` |
| `db_username` | Master username | `postgres` |
| `db_password` | Master password (empty = generate) | (empty) |
| `alert_email` | SES identity for alerts | (required) |
| `backend_source_path` | Path to backend code | `../backend` |

## Outputs

- **api_base_url** — Base URL for the REST API
- **api_endpoints** — Map of paths (tools, trend, aws, alerts, export)
- **rds_endpoint** — RDS hostname
- **db_secret_arn** — ARN of the DB credentials secret
- **api_keys_secret_arn** — ARN for optional API keys secret
- **lambda_functions** — List of Lambda function names
- **vpc_id** — VPC ID
- **alert_email_identity** — SES email identity

## IAM

Lambdas use a single IAM role with:

- **AWSLambdaVPCAccessExecutionRole** — CloudWatch Logs + VPC ENI
- **secretsmanager:GetSecretValue** — DB secret (and optional API keys)
- **ses:SendEmail** / **ses:SendRawEmail** — Alerts (CheckAlerts)
- **ce:GetCostAndUsage** — AWS Cost Explorer (FetchBilling)

## Optional: existing VPC

Set `vpc_id`, `private_subnet_ids`, and `public_subnet_ids` to use an existing VPC instead of creating one.
