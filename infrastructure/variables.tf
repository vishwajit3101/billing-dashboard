# -----------------------------------------------------------------------------
# Billing Watch Backend — Terraform variables
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Environment name (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDRs for private subnets (Lambda, RDS)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDRs for public subnets (NAT Gateway)"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "billing_watch"
}

variable "db_username" {
  description = "Master username for RDS"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS (leave empty to auto-generate)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_allocated_storage_gb" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 20
}

# -----------------------------------------------------------------------------
# Lambda
# -----------------------------------------------------------------------------
variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Lambda memory in MB"
  type        = number
  default     = 256
}

variable "backend_source_path" {
  description = "Path to backend source code (relative to this dir or absolute)"
  type        = string
  default     = "../backend"
}

# -----------------------------------------------------------------------------
# SES (alerts)
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email address for billing alerts (SES identity)"
  type        = string
}

variable "ses_region" {
  description = "Region for SES (use us-east-1 for sandbox)"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Optional: existing VPC/Subnets (set to use existing network)
# -----------------------------------------------------------------------------
variable "vpc_id" {
  description = "Existing VPC ID (leave empty to create new VPC)"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Existing private subnet IDs (required if vpc_id is set)"
  type        = list(string)
  default     = []
}

variable "public_subnet_ids" {
  description = "Existing public subnet IDs for NAT (required if vpc_id is set)"
  type        = list(string)
  default     = []
}
