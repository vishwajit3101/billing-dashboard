# -----------------------------------------------------------------------------
# Billing Watch Backend — Terraform main configuration
# VPC, RDS PostgreSQL, Lambda (5), API Gateway, EventBridge, Secrets Manager, SES
# -----------------------------------------------------------------------------

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# DB password (generate if not provided)
# -----------------------------------------------------------------------------
resource "random_password" "db" {
  count   = var.db_password != "" ? 0 : 1
  length  = 24
  special = false
}

locals {
  db_password = var.db_password != "" ? var.db_password : random_password.db[0].result
  name_prefix = "billing-watch-${var.environment}"
}

# -----------------------------------------------------------------------------
# VPC and networking
# -----------------------------------------------------------------------------
resource "aws_vpc" "main" {
  count                = var.vpc_id == "" ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  count  = var.vpc_id == "" ? 1 : 0
  vpc_id = aws_vpc.main[0].id
  tags   = { Name = "${local.name_prefix}-igw" }
}

# Private subnets (Lambda, RDS)
resource "aws_subnet" "private" {
  count             = var.vpc_id == "" ? length(var.private_subnet_cidrs) : 0
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = { Name = "${local.name_prefix}-private-${count.index + 1}" }
}

# Public subnets (NAT)
resource "aws_subnet" "public" {
  count                   = var.vpc_id == "" ? length(var.public_subnet_cidrs) : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${local.name_prefix}-public-${count.index + 1}" }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# NAT Gateway (so Lambda in private subnet can reach internet)
resource "aws_eip" "nat" {
  count  = var.vpc_id == "" ? 1 : 0
  domain = "vpc"
  tags   = { Name = "${local.name_prefix}-nat-eip" }
}

resource "aws_nat_gateway" "main" {
  count         = var.vpc_id == "" ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  tags          = { Name = "${local.name_prefix}-nat" }
}

resource "aws_route_table" "private" {
  count  = var.vpc_id == "" ? 1 : 0
  vpc_id = aws_vpc.main[0].id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }
  tags = { Name = "${local.name_prefix}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = var.vpc_id == "" ? length(aws_subnet.private) : 0
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

resource "aws_route_table" "public" {
  count  = var.vpc_id == "" ? 1 : 0
  vpc_id = aws_vpc.main[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }
  tags = { Name = "${local.name_prefix}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = var.vpc_id == "" ? length(aws_subnet.public) : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

locals {
  vpc_id             = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id
  private_subnet_ids = var.vpc_id != "" ? var.private_subnet_ids : aws_subnet.private[*].id
  public_subnet_ids  = var.vpc_id != "" ? var.public_subnet_ids : aws_subnet.public[*].id
}

# -----------------------------------------------------------------------------
# Security groups
# -----------------------------------------------------------------------------
resource "aws_security_group" "lambda" {
  name_prefix = "${local.name_prefix}-lambda-"
  description = "Lambda functions (Dashboard API + jobs)"
  vpc_id      = local.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-lambda-sg" }
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  description = "RDS PostgreSQL"
  vpc_id      = local.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-rds-sg" }
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = local.private_subnet_ids
  tags       = { Name = "${local.name_prefix}-db-subnet" }
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = local.db_password

  allocated_storage     = var.db_allocated_storage_gb
  max_allocated_storage = 100
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = false
  publicly_accessible    = false

  skip_final_snapshot = var.environment != "prod"
  tags                = { Name = "${local.name_prefix}-db" }
}

# -----------------------------------------------------------------------------
# Secrets Manager — DB credentials for Lambdas
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db" {
  name        = "${local.name_prefix}/db"
  description = "RDS credentials for Billing Watch Lambdas"
  tags        = { Name = "${local.name_prefix}-db-secret" }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
    username = aws_db_instance.main.username
    password = local.db_password
  })
}

# -----------------------------------------------------------------------------
# Lambda deployment package (source only; optional layer adds psycopg2)
# Before first apply, run: ./scripts/build-layer.sh (or: pip install -t build/layer/python psycopg2-binary && cd build/layer && zip -r ../layer.zip .)
# -----------------------------------------------------------------------------
data "archive_file" "backend" {
  type        = "zip"
  source_dir  = "${path.module}/${var.backend_source_path}"
  output_path = "${path.module}/build/backend.zip"
  excludes    = ["__pycache__", "*.pyc", ".git", "build", "tests", "*.md", "*.zip"]
}

# Optional: dependency layer (psycopg2). Create build/layer.zip with scripts/build-layer.sh first.
resource "aws_lambda_layer_version" "deps" {
  count               = fileexists("${path.module}/build/layer.zip") ? 1 : 0
  filename            = "${path.module}/build/layer.zip"
  layer_name          = "${local.name_prefix}-deps"
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256("${path.module}/build/layer.zip")
}

# -----------------------------------------------------------------------------
# IAM role and policies for Lambdas
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Basic Lambda execution (logs, VPC ENI)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Secrets Manager read
resource "aws_iam_role_policy" "lambda_secrets" {
  name   = "secrets"
  role   = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.db.arn]
    }]
  })
}

# SES send (for CheckAlerts)
resource "aws_iam_role_policy" "lambda_ses" {
  name   = "ses"
  role   = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ses:SendEmail", "ses:SendRawEmail"]
      Resource = "*"
    }]
  })
}

# Cost Explorer read (for FetchBilling / AWS spend)
resource "aws_iam_role_policy" "lambda_ce" {
  name   = "cost-explorer"
  role   = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ce:GetCostAndUsage", "ce:GetCostForecast"]
      Resource = "*"
    }]
  })
}

# -----------------------------------------------------------------------------
# Lambda functions (5)
# -----------------------------------------------------------------------------
locals {
  lambda_env = {
    DB_SECRET_ARN = aws_secretsmanager_secret.db.arn
    ALERT_EMAIL   = var.alert_email
  }
  lambda_layer_arn = fileexists("${path.module}/build/layer.zip") ? [aws_lambda_layer_version.deps[0].arn] : []
  lambda_common = {
    runtime          = var.lambda_runtime
    timeout          = var.lambda_timeout_seconds
    memory_size      = var.lambda_memory_mb
    role             = aws_iam_role.lambda.arn
    handler          = "placeholder"
    source_code_hash = data.archive_file.backend.output_base64sha256
    filename         = data.archive_file.backend.output_path
    layers           = local.lambda_layer_arn
    vpc_config = {
      subnet_ids         = local.private_subnet_ids
      security_group_ids = [aws_security_group.lambda.id]
    }
  }
}

resource "aws_lambda_function" "fetch_billing" {
  function_name = "${local.name_prefix}-fetch-billing"
  handler       = "src.jobs.fetch_billing.handler"
  environment {
    variables = local.lambda_env
  }
  runtime          = local.lambda_common.runtime
  timeout          = local.lambda_common.timeout
  memory_size      = local.lambda_common.memory_size
  role             = local.lambda_common.role
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  layers           = local.lambda_common.layers
  vpc_config {
    subnet_ids         = local.lambda_common.vpc_config.subnet_ids
    security_group_ids = local.lambda_common.vpc_config.security_group_ids
  }
}

resource "aws_lambda_function" "fetch_posthog" {
  function_name = "${local.name_prefix}-fetch-posthog"
  handler       = "src.jobs.fetch_posthog.handler"
  environment { variables = local.lambda_env }
  runtime          = local.lambda_common.runtime
  timeout          = local.lambda_common.timeout
  memory_size      = local.lambda_common.memory_size
  role             = local.lambda_common.role
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  layers           = local.lambda_common.layers
  vpc_config {
    subnet_ids         = local.lambda_common.vpc_config.subnet_ids
    security_group_ids = local.lambda_common.vpc_config.security_group_ids
  }
}

resource "aws_lambda_function" "compute_usage" {
  function_name = "${local.name_prefix}-compute-usage"
  handler       = "src.jobs.compute_usage.handler"
  environment { variables = local.lambda_env }
  runtime          = local.lambda_common.runtime
  timeout          = local.lambda_common.timeout
  memory_size      = local.lambda_common.memory_size
  role             = local.lambda_common.role
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  layers           = local.lambda_common.layers
  vpc_config {
    subnet_ids         = local.lambda_common.vpc_config.subnet_ids
    security_group_ids = local.lambda_common.vpc_config.security_group_ids
  }
}

resource "aws_lambda_function" "check_alerts" {
  function_name = "${local.name_prefix}-check-alerts"
  handler       = "src.jobs.check_alerts.handler"
  environment { variables = local.lambda_env }
  runtime          = local.lambda_common.runtime
  timeout          = local.lambda_common.timeout
  memory_size      = local.lambda_common.memory_size
  role             = local.lambda_common.role
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  layers           = local.lambda_common.layers
  vpc_config {
    subnet_ids         = local.lambda_common.vpc_config.subnet_ids
    security_group_ids = local.lambda_common.vpc_config.security_group_ids
  }
}

resource "aws_lambda_function" "dashboard_api" {
  function_name = "${local.name_prefix}-dashboard-api"
  handler       = "lambda_functions.dashboard_api.handler.handler"
  environment { variables = local.lambda_env }
  runtime          = local.lambda_common.runtime
  timeout          = local.lambda_common.timeout
  memory_size      = local.lambda_common.memory_size
  role             = local.lambda_common.role
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  layers           = local.lambda_common.layers
  vpc_config {
    subnet_ids         = local.lambda_common.vpc_config.subnet_ids
    security_group_ids = local.lambda_common.vpc_config.security_group_ids
  }
}

# -----------------------------------------------------------------------------
# EventBridge + Step Functions orchestration → see eventbridge.tf
# - Every hour at :00 → pipeline (billing_fetcher + posthog_processor at :05, then risk_calculator, alert_engine)
# - API Lambda is always available via API Gateway (no schedule)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# API Gateway REST API
# -----------------------------------------------------------------------------
resource "aws_apigatewayv2_api" "main" {
  name          = local.name_prefix
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
  }
}

# For HTTP API we use integrations; for REST API we'd use aws_api_gateway_*. 
# Using HTTP API (v2) is simpler and supports Lambda proxy.
resource "aws_apigatewayv2_integration" "dashboard" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.dashboard_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "tools" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/tools"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard.id}"
}

resource "aws_apigatewayv2_route" "tool_trend" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/tools/{tool_id}/trend"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard.id}"
}

resource "aws_apigatewayv2_route" "aws_spend" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/aws/spend"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard.id}"
}

resource "aws_apigatewayv2_route" "alerts" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/alerts"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard.id}"
}

resource "aws_apigatewayv2_route" "export" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/export"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# -----------------------------------------------------------------------------
# SES email identity (for alerts)
# -----------------------------------------------------------------------------
resource "aws_sesv2_email_identity" "alert" {
  email_identity = var.alert_email
}

# -----------------------------------------------------------------------------
# Optional: Secrets Manager secret for API keys (tool keys, PostHog, etc.)
# Create the secret; populate keys outside Terraform or via CI.
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "api_keys" {
  name        = "${local.name_prefix}/api-keys"
  description = "API keys for Anthropic, Tavily, FullEnrich, Buyercaddy, PostHog (optional)"
  tags        = { Name = "${local.name_prefix}-api-keys" }
}
