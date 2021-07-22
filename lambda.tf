resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.uptime.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.uptime_lambda.arn

}

resource "aws_lambda_function" "uptime" {
  function_name    = var.function_name
  filename         = "${local.filename}.zip"
  source_code_hash = data.archive_file.function.output_base64sha256

  role    = aws_iam_role.lambda.arn
  handler = "start_stop_rds.lambda_handler"
  runtime = "python3.8"
  timeout = var.timeout

  environment {
    variables = local.env_variables
  }

  tags = var.lambda_tags

  depends_on = [data.archive_file.function]
}
