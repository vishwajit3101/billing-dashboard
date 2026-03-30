provider "aws" {
  region = var.aws_region
}

resource "aws_lambda_function" "billing_fetcher" {
  filename      = "backend/billing-hourly-fetch.zip"
  function_name = "billing_watch_fetcher"
  role          = aws_iam_role.lambda_role.arn
  handler       = "app.fetch_data_lambda.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      DB_HOST              = var.db_host
      DB_PORT              = var.db_port
      DB_NAME              = var.db_name
      DB_USER              = var.db_user
      DB_PASSWORD          = var.db_password
      AWS_REGION           = var.aws_region
      AWS_MONTHLY_BUDGET   = var.aws_monthly_budget
      POSTHOG_API_KEY      = var.posthog_api_key
      POSTHOG_PROJECT_ID   = var.posthog_project_id
      POSTHOG_HOST         = var.posthog_host
      POSTHOG_PERSONAL_API_KEY = var.posthog_personal_api_key
      TAVILY_API_KEY       = var.tavily_api_key
      ANTHROPIC_ADMIN_KEY  = var.anthropic_admin_key
      ANTHROPIC_ORG_ID     = var.anthropic_org_id
      FULLENRICH_API_KEY   = var.fullenrich_api_key
      BUYERCADDY_API_KEY   = var.buyercaddy_api_key
      ALERT_EMAIL_SENDER   = var.alert_email_sender
      ALERT_EMAIL_RECIPIENT = var.alert_email_recipient
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "billing_watch_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# Add Cost Explorer and SES permissions to the role
resource "aws_iam_role_policy" "lambda_policy" {
  name = "billing_watch_lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ce:GetCostAndUsage",
          "ses:SendEmail",
          "ses:SendRawEmail",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
# Trigger Lambda every hour
resource "aws_cloudwatch_event_rule" "hourly_fetch" {
  name                = "billing-watch-hourly-fetch"
  description         = "Trigger billing data fetch every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "fetch_target" {
  rule      = aws_cloudwatch_event_rule.hourly_fetch.name
  target_id = "billing_fetcher"
  arn       = aws_lambda_function.billing_fetcher.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.billing_fetcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_fetch.arn
}
