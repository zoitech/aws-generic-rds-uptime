# triggering the uptime lambda
resource "aws_cloudwatch_event_rule" "uptime_lambda" {
  name                = "trigger-lambda-${var.function_name}"
  description         = "Trigger the lambda ${var.function_name}"
  schedule_expression = "cron(${var.schedule})"
  state          = local.enable_schedule
}

resource "aws_cloudwatch_event_target" "uptime_lambda" {
  rule      = aws_cloudwatch_event_rule.uptime_lambda.name
  target_id = "TriggerLambdaRDSUptimeFunction"
  arn       = aws_lambda_function.uptime.arn
}

# log group
resource "aws_cloudwatch_log_group" "rds_uptime" {
  name              = local.rds_uptime_log_group
  retention_in_days = var.cloudwatch_log_retention_in_days

  tags = {
    creation = "terraform"
  }
}

# lambda function monitoring/alarms
## General lambda execution error
resource "aws_cloudwatch_metric_alarm" "lambda_execution_error" {
  alarm_name          = "${var.account_alias}-lambda-${var.function_name}_Execution-Error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"

  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  datapoints_to_alarm = 1

  dimensions = {
    FunctionName = var.function_name
  }

  alarm_description = "Monitors if ${var.function_name} failed to execute"
  alarm_actions     = [aws_sns_topic.alarm_rds_uptime.arn]

  tags = var.cwma_tags
}

## General lambda invocation error
resource "aws_cloudwatch_metric_alarm" "lambda_invocation_error" {
  alarm_name          = "${var.account_alias}-lambda-${var.function_name}_Hourly-Invocation-Error"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  namespace           = "AWS/Lambda"
  metric_name         = "Invocations"

  # with breaching 2 additional previous points are referenced before checking
  # so 3 total = 1hour/3= 20 mins. 
  # 20 mins = 1200 seconds
  # additonal 6 minutes for run time. 6/3 = 2 additional minutes per check = 120 seconds
  # 1200 + 120 = 1320
  # the check will happen after 3x1320 seconds = 1 hour and 6 mins
  period              = "1320"
  statistic           = "Sum"
  threshold           = "1"
  treat_missing_data  = "breaching"
  datapoints_to_alarm = 1

  dimensions = {
    FunctionName = var.function_name
  }

  alarm_description = "Monitors if ${var.function_name} has stopped executing hourly"
  alarm_actions     = [aws_sns_topic.alarm_rds_uptime.arn]

  tags = var.cwma_tags
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

  depends_on = [
    aws_cloudwatch_log_group.rds_uptime,
  ]
}

resource "aws_cloudwatch_metric_alarm" "lambda_python_error" {
  alarm_name          = "${var.account_alias}-lambda-${var.function_name}_Python-Error"
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

  alarm_description = "Monitors if ${var.function_name} contains a python error"
  alarm_actions     = [aws_sns_topic.alarm_rds_uptime.arn]

  tags = var.cwma_tags
}
