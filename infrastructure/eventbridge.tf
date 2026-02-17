# -----------------------------------------------------------------------------
# EventBridge + Step Functions orchestration
# Flow: :00 billing_fetcher | :05 posthog_processor (parallel) → risk_calculator → alert_engine
# API Lambda is always available via API Gateway (no schedule).
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CloudWatch Logs for Step Functions (monitoring)
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "stepfunction" {
  name              = "/aws/stepfunctions/${local.name_prefix}-pipeline"
  retention_in_days  = var.environment == "prod" ? 30 : 7
  tags              = { Name = "${local.name_prefix}-sfn-logs" }
}

# -----------------------------------------------------------------------------
# IAM role for Step Functions (invoke Lambdas + write logs)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "stepfunction" {
  name = "${local.name_prefix}-stepfunction-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "states.${var.aws_region}.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "stepfunction_lambda" {
  name   = "invoke-lambda"
  role   = aws_iam_role.stepfunction.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [
          aws_lambda_function.fetch_billing.arn,
          aws_lambda_function.fetch_posthog.arn,
          aws_lambda_function.compute_usage.arn,
          aws_lambda_function.check_alerts.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunction_logs" {
  name   = "cloudwatch-logs"
  role   = aws_iam_role.stepfunction.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery", "logs:DeleteLogDelivery", "logs:ListLogDeliveries", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies", "logs:DescribeLogGroups"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:PutLogEvents", "logs:PutResourcePolicy", "logs:DescribeLogStreams"]
        Resource = "${aws_cloudwatch_log_group.stepfunction.arn}:*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Step Functions state machine (pipeline definition with retries)
# -----------------------------------------------------------------------------
resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.name_prefix}-pipeline"
  role_arn = aws_iam_role.stepfunction.arn
  definition = templatefile(
    "${path.module}/../backend/lambda_functions/orchestrator/stepfunction.json",
    {
      fetch_billing_arn  = aws_lambda_function.fetch_billing.arn
      fetch_posthog_arn  = aws_lambda_function.fetch_posthog.arn
      compute_usage_arn  = aws_lambda_function.compute_usage.arn
      check_alerts_arn   = aws_lambda_function.check_alerts.arn
    }
  )
  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunction.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }
  type = "STANDARD"
  tags = { Name = "${local.name_prefix}-pipeline" }
}

# Allow Step Functions to invoke the four Lambdas
resource "aws_lambda_permission" "stepfunction_fetch_billing" {
  statement_id  = "AllowStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fetch_billing.function_name
  principal     = "states.${var.aws_region}.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}

resource "aws_lambda_permission" "stepfunction_fetch_posthog" {
  statement_id  = "AllowStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fetch_posthog.function_name
  principal     = "states.${var.aws_region}.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}

resource "aws_lambda_permission" "stepfunction_compute_usage" {
  statement_id  = "AllowStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.compute_usage.function_name
  principal     = "states.${var.aws_region}.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}

resource "aws_lambda_permission" "stepfunction_check_alerts" {
  statement_id  = "AllowStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_alerts.function_name
  principal     = "states.${var.aws_region}.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}

# -----------------------------------------------------------------------------
# EventBridge rule: every hour at :00 → start Step Function
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "pipeline_hourly" {
  name                = "${local.name_prefix}-pipeline-hourly"
  description         = "Start billing pipeline every hour at :00 (billing_fetcher at :00, posthog_processor at :05, then risk_calculator, alert_engine)"
  schedule_expression = "cron(0 * * * ? *)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "stepfunction" {
  rule      = aws_cloudwatch_event_rule.pipeline_hourly.name
  target_id = "BillingWatchPipeline"
  arn       = aws_sfn_state_machine.pipeline.arn
  role_arn  = aws_iam_role.eventbridge_sfn.arn
  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 2
  }
  input = "{}"
}

# IAM role so EventBridge can start Step Functions executions
resource "aws_iam_role" "eventbridge_sfn" {
  name = "${local.name_prefix}-eventbridge-sfn"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name   = "start-execution"
  role   = aws_iam_role.eventbridge_sfn.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = aws_sfn_state_machine.pipeline.arn
    }]
  })
}
