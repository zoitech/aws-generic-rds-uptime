resource "aws_iam_role" "lambda" {
  count = local.create_rds_uptime_resources
  name  = var.function_role_name

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "basic" {
  count       = local.create_rds_uptime_resources
  name        = "${var.function_role_name}_execution"
  description = "Basic Exec policy"
  policy      = local.role_permissions
}

resource "aws_iam_policy" "logging" {
  count       = local.create_rds_uptime_resources
  name        = "${var.function_role_name}_logging"
  description = "Logging policy"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
          "Action": [
              "logs:CreateLogGroup",
              "logs:CreateLogStream",
              "logs:PutLogEvents",
              "logs:TagResource",
              "logs:ListTagsForResource"
          ],
          "Resource": "arn:aws:logs:*:*:*",
          "Effect": "Allow"
      }
      ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "basic_exec" {
  count      = local.create_rds_uptime_resources
  role       = aws_iam_role.lambda[count.index].name
  policy_arn = aws_iam_policy.basic[count.index].arn
}

resource "aws_iam_role_policy_attachment" "basic_logging" {
  count      = local.create_rds_uptime_resources
  role       = aws_iam_role.lambda[count.index].name
  policy_arn = aws_iam_policy.logging[count.index].arn
}
