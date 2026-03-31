variable "aws_region" {
  default = "ap-south-1"
}

variable "db_host" {
  type = string
}

variable "db_name" {
  default = "billing_watch"
}

variable "db_user" {
  default = "postgres"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "posthog_api_key" {
  type      = string
  sensitive = true
}

variable "tavily_api_key" {
  type      = string
  sensitive = true
}

variable "db_port" {
  default = "5432"
}

variable "aws_monthly_budget" {
  default = "174.56"
}

variable "posthog_project_id" {
  type = string
}

variable "posthog_host" {
  default = "https://us.i.posthog.com"
}

variable "posthog_personal_api_key" {
  type      = string
  sensitive = true
}

variable "anthropic_admin_key" {
  type      = string
  sensitive = true
}

variable "anthropic_org_id" {
  type = string
}

variable "fullenrich_api_key" {
  type      = string
  sensitive = true
}

variable "buyercaddy_api_key" {
  type      = string
  sensitive = true
}

variable "sqs_queue_url" {
  type = string
}

variable "alert_email_sender" {
  default = "billing@operator.ai"
}

variable "alert_email_recipient" {
  default = "admin@operator.ai"
}

variable "dashboard_url" {
  default = "http://localhost:8080"
}
