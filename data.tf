data "aws_caller_identity" "current" {
}

data "aws_iam_account_alias" "current" {}

data "archive_file" "function" {
  type        = "zip"
  source_dir  = "${path.module}/function/"
  output_path = "${local.filename}.zip"
}
