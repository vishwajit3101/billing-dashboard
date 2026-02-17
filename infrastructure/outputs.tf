# -----------------------------------------------------------------------------
# Billing Watch Backend — Terraform outputs
# -----------------------------------------------------------------------------

output "api_base_url" {
  description = "Base URL for the Billing Dashboard API (append e.g. /api/tools, /api/aws/spend)"
  value       = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}"
}

output "api_endpoints" {
  description = "Key API paths for the frontend"
  value = {
    tools   = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}/api/tools"
    trend  = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}/api/tools/{tool_id}/trend"
    aws    = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}/api/aws/spend"
    alerts = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}/api/alerts"
    export = "https://${aws_apigatewayv2_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_apigatewayv2_stage.default.name}/api/export"
  }
}

output "rds_endpoint" {
  description = "RDS PostgreSQL instance endpoint (hostname)"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN for DB credentials (used by Lambdas)"
  value       = aws_secretsmanager_secret.db.arn
}

output "api_keys_secret_arn" {
  description = "Secrets Manager ARN for optional API keys (Anthropic, Tavily, etc.)"
  value       = aws_secretsmanager_secret.api_keys.arn
}

output "lambda_functions" {
  description = "Names of deployed Lambda functions"
  value = [
    aws_lambda_function.fetch_billing.function_name,
    aws_lambda_function.fetch_posthog.function_name,
    aws_lambda_function.compute_usage.function_name,
    aws_lambda_function.check_alerts.function_name,
    aws_lambda_function.dashboard_api.function_name,
  ]
}

output "vpc_id" {
  description = "VPC ID used by RDS and Lambdas"
  value       = local.vpc_id
}

output "alert_email_identity" {
  description = "SES email identity used for billing alerts"
  value       = aws_sesv2_email_identity.alert.email_identity
}

# -----------------------------------------------------------------------------
# Orchestration (EventBridge + Step Functions)
# -----------------------------------------------------------------------------
output "stepfunction_arn" {
  description = "Step Functions state machine ARN (billing pipeline)"
  value       = aws_sfn_state_machine.pipeline.arn
}

output "pipeline_schedule_rule" {
  description = "EventBridge rule name that triggers the pipeline (cron: every hour at :00)"
  value       = aws_cloudwatch_event_rule.pipeline_hourly.name
}

output "stepfunction_log_group" {
  description = "CloudWatch Logs group for pipeline execution history"
  value       = aws_cloudwatch_log_group.stepfunction.name
}
