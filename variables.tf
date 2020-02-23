# cloud watch
variable "enable_schedule" {
  type        = bool
  default     = true
  description = "Defines if the function should be scheduled to run."
}

variable "schedule" {
  type        = string
  default     = "0 * * * ? *" # (every hour)
  description = "When cloudwatch will trigger the function ."
}

# iam
variable "function_role_name" {
  type        = string
  description = "The name of the function role."
  default     = "lambda-svc-rds-uptime"
}

variable "role_permissions" {
  type        = string
  description = "The permissions of the function gets."
  default     = ""
}

# lambda
variable "function_name" {
  type        = string
  description = "The name of the function"
  default     = "svc-rds-uptime"
}

variable "timeout" {
  type        = string
  default     = "180"
  description = "How long the lambda should run before being stopped in seconds"
}

# lambda environment variables
variable "env_uptime_variables" {
  description = "A map of the required environment variables"
  type        = map(string)
  default = {
    UPTIME_24x7    = "4-n;4-n;4-n;4-n;4-n;4-n;4-n"
    UPTIME_0x7     = "n-20;n-20;n-20;n-20;n-20;n-20;n-20"
    UPTIME_24x5    = "4-n;4-n;4-n;4-n;4-20;n-20;n-20"
    UPTIME_24x6    = "4-n;4-n;4-n;4-n;4-n;4-20;n-20"
    UPTIME_14x5    = "4-20;4-20;4-20;4-20;4-20;n-20;n-20"
    UPTIME_14x6    = "4-20;4-20;4-20;4-20;4-n;4-20;n-20"
    UPTIME_DEFAULT = "n-n;n-n;n-n;n-n;n-n;n-n;n-n"
  }
}

variable "env_uptime_tag_name_variable" {
  description = "Uptime tag name"
  type        = string
  default     = "uptime"
}

variable "env_mode_variable" {
  description = "Enforce or set lambda to permissive"
  type        = string
  default     = "ENFORCE" #"PERMISSIVE"
}


# Tags
variable "cwma_tags" {
  description = "Tags for the cloud watch metric alarms"
  type        = map(string)
  default = {
    test = "test"
  }
}

variable "lambda_tags" {
  description = "Tags for the lambda function"
  type        = map(string)
  default     = {}
}

variable "sns_tags" {
  description = "Tags for the SNS topic"
  type        = map(string)
  default     = {}
}
