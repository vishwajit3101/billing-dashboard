provider "aws" {
  region = var.aws_region
}

resource "aws_lambda_function" "billing_fetcher" {
  filename      = "backend/billing-hourly-fetch.zip"
  function_name = "billing_watch_fetcher"
  role          = aws_iam_role.lambda_role.arn
  handler       = "app.lambda_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
      POSTHOG_API_KEY = var.posthog_api_key
      TAVILY_API_KEY = var.tavily_api_key
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
