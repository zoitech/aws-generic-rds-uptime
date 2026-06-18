locals {
  #filename         = replace(replace(var.source_data, "/", "_"), "\\", "_")
  create_rds_uptime_resources = (var.enable_rds_uptime_module ? 1 : 0)
  filename                    = "rdsuptimefunction"
  enable_schedule             = (var.enable_schedule == true ? "ENABLED" : "DISABLED")
  role_permissions            = (var.role_permissions == "" ? file("${path.module}/svc_rds_uptime.json") : var.role_permissions)

  # cloudwatch
  # log group
  rds_uptime_log_group = "/aws/lambda/${var.function_name}"

  # sns
  sns_topic_name_rds_uptime = "lambda-${var.function_name}-error"

  # lambda environment variables
  env_variables = merge(var.env_uptime_variables, local.env_uptime_tag_name_variable, local.env_mode_variable)

  env_uptime_tag_name_variable = {
    UPTIME_TAG = var.env_uptime_tag_name_variable
  }

  env_mode_variable = {
    MODE = var.env_mode_variable #"PERMISSIVE"
  }
}
