variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "fastapi-user-management"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "github_repository" {
  type        = string
  description = "owner/repository used by GitHub Actions OIDC"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "acm_certificate_arn" {
  type        = string
  default     = null
  nullable    = true
  description = "ACM certificate ARN for HTTPS. Required when enable_https=true."
}

variable "enable_https" {
  type        = bool
  default     = true
  description = "Expose the ALB over HTTPS and redirect HTTP to HTTPS."
}

variable "min_capacity" {
  type    = number
  default = 2
}

variable "max_capacity" {
  type    = number
  default = 6
}
