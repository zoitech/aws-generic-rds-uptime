# triggering the uptime lambda
resource "aws_cloudwatch_event_rule" "cron" {
  count               = local.enable_schedule
  name                = "trigger-lambda-${var.function_name}"
  description         = "Trigger the lambda ${var.function_name}"
  schedule_expression = "cron(${var.schedule})"
}

resource "aws_cloudwatch_event_target" "uptime_lambda" {
  count     = local.enable_schedule
  rule      = aws_cloudwatch_event_rule.cron[0].name
  target_id = "TriggerLambdaRDSUptimeFunction"
  arn       = aws_lambda_function.uptime.arn
}

# log group
resource "aws_cloudwatch_log_group" "rds_uptime" {
  name = local.rds_uptime_log_group

  tags = {
    creation   = "terraform"
    department = "zoi"
  }
}

# lambda function monitoring/alarms
## General lambda execution error
resource "aws_cloudwatch_metric_alarm" "lambda_execution_error" {
  alarm_name          = "${data.aws_iam_account_alias.current.account_alias}-lambda-${var.function_name}_Execution-Error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"

  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  datapoints_to_alarm = 1

  # dimensions = {
  #   LogGroupName = 
  #   DestinationType =
  #   FilterName =
  # }

  alarm_description = "Lambda RDS uptime error"
  alarm_actions     = [aws_sns_topic.rds_uptime.arn]
}

## python specific errors
### python error in script somewhere
resource "aws_cloudwatch_log_metric_filter" "lambda_python_error" {
  name           = "lambda-rds-uptime_python-error"
  pattern        = "?Error ?error ?ERROR"
  log_group_name = "/aws/lambda/${var.function_name}"

  metric_transformation {
    namespace = "LogMetrics"
    name      = "lambda-rds-uptime_python-error"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_python_error" {
  alarm_name          = "${data.aws_iam_account_alias.current.account_alias}-lambda-${var.function_name}_python-error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  namespace           = "LogMetrics"
  metric_name         = aws_cloudwatch_log_metric_filter.lambda_python_error.name

  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  datapoints_to_alarm = 1

  # dimensions = {
  #   LogGroupName = 
  #   DestinationType =
  #   FilterName =
  # }

  alarm_description = "This metric alarm monitors errors in the rds uptime python script"
  alarm_actions     = [aws_sns_topic.rds_uptime.arn]
}
