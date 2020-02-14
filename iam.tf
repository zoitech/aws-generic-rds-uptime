resource "aws_iam_role" "lambda" {
  name = var.function_role_name

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
  name        = "${var.function_role_name}_execution"
  description = "Basic Exec policy"
  policy      = local.role_permissions
}

resource "aws_iam_policy" "logging" {
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
              "logs:PutLogEvents"
          ],
          "Resource": "arn:aws:logs:*:*:*",
          "Effect": "Allow"
      }
      ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "basic_exec" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.basic.arn
}

resource "aws_iam_role_policy_attachment" "basic_logging" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.logging.arn
}
