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
