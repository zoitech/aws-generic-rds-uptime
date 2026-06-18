# terraform-aws-rds-uptime
Lambda function for managing RDS uptimes

## Description

Terraform module which uses lambda for managing RDS uptimes.

The following resources are creating via this module:

* Lambda function
* IAM Role
* IAM Policy
* Cloudwatch Event
* Cloudwatch Alarm
* SNS Topic

## Usage

```hcl
module "rds_uptime" {
  source = "git::https://git.zoi.de/generic/tf-modules/aws-generic-rds-uptime.git?ref=3.3.0"
  account_alias     = "ak-project-name"
  region            = "eu-central-1"
```
### Enable/Disable module

By default, this module is enabled. To disable the creation of all resources within this module, set the variable `enable_ec2_uptime_module` to `false`.

```hcl
module "rds_uptime" {
  source = "..."

  enable_rds_uptime_module = false
}
```


It is possible to amend most variables such as schedule, names etc if desired:

```hcl
module "rds_uptime" {
  source = "git::https://git.zoi.de/generic/tf-modules/aws-generic-rds-uptime.gitref=3.3.0"
  # cloudwatch
  enable_schedule = true
  schedule = "0 * * * ? *"
  # sns
  sns_topic_name_rds_uptime = "rds-uptime"
  # iam
  function_role_name = "lambda-rds-uptime"
  # lambda
  function_name                = "rds-uptime"
  timeout                      = "180"
  env_uptime_variables         = = {
    UPTIME_24x7    = "4-n;4-n;4-n;4-n;4-n;4-n;4-n"
    UPTIME_0x7     = "n-20;n-20;n-20;n-20;n-20;n-20;n-20"
    UPTIME_24x5    = "4-n;4-n;4-n;4-n;4-20;n-20;n-20"
    UPTIME_24x6    = "4-n;4-n;4-n;4-n;4-n;4-20;n-20"
    UPTIME_14x5    = "4-20;4-20;4-20;4-20;4-20;n-20;n-20"
    UPTIME_14x6    = "4-20;4-20;4-20;4-20;4-n;4-20;n-20"
    UPTIME_DEFAULT = "n-n;n-n;n-n;n-n;n-n;n-n;n-n"
  }
  env_uptime_tag_name_variable = "uptime"
  env_mode_variable            = "ENFORCE"
}
```

### Cron Job Schedule

By default "schedule" is set to "0 * * * ? *", which will cause cloudwatch to trigger the lambda once every hour on the hour.

### Lambda Uptime Environment Variable Values

The following uptime tag values are defined and evaluated by default via the variable "env_uptime_variables" (within lambda environment variables):

* UPTIME_24x7    = "4-n;4-n;4-n;4-n;4-n;4-n;4-n"
* UPTIME_0x7     = "n-20;n-20;n-20;n-20;n-20;n-20;n-20"
* UPTIME_24x5    = "4-n;4-n;4-n;4-n;4-20;n-20;n-20"
* UPTIME_24x6    = "4-n;4-n;4-n;4-n;4-n;4-20;n-20"
* UPTIME_14x5    = "4-20;4-20;4-20;4-20;4-20;n-20;n-20"
* UPTIME_14x6    = "4-20;4-20;4-20;4-20;4-n;4-20;n-20"
* UPTIME_DEFAULT = "n-n;n-n;n-n;n-n;n-n;n-n;n-n"

There are 7 blocks (mo-so) sperated by a ";".  
The left hand side of the block describes the start time, and the right hand side the stop time.  
A value of "n" implies the server's start or stop time should not be checked or handled.  


Examples:
- `8-n`: start at 8am, never stops.
- `8-22`: start at 8am, stops at 10pm.
- `n-22`: never start, stops at 10pm.


If no valid uptime is configured in the RDS "uptime" tag (does not match the lambda uptime environment variables), **the UPTIME_DEFAULT = "n-n;n-n;n-n;n-n;n-n;n-n;n-n"** will be used. This will **not** start or stop an RDS instance.

```UPTIME_<Alias>```: The resolution of an alias in the "uptime"'s tag value such as 24x7, will result to: (UPTIME_24x7).

#### Enforce/Permissive Mode

By default the variable "env_mode_variable" is set to "PERMISSIVE". This can also be set to "ENFORCE". Permissive will prevent the lambda function from starting or stopping all RDS instances.

### RDS Uptime Tag

RDS instances are managed via their "uptime" tag. By default the tag key's name is "uptime", but this can be changed if you desire.

Based on the default configuration mentioned above, the following values would be supported in an RDS' "uptime" tag:

```hcl
24x7
0x7
24x5
24x6
14x5
14x6
```

### Monitoring and Alerts

Three cloudwatch alarms are created which monitor if the uptime lambda is executing regularly, is executing without errors and checking no python errors are generated. If a cloudwatch alarm goes into alarm status, an alert is sent to an SNS topic. Depending on who or which group email is subscribed to the SNS topic, they will receive any alarm notifications via email.

Currently it is no possible to automatically subscribe emails to an SNS topic via terraform, so subscriptions must be made manually. Please refer to [The issue topic here](https://github.com/pulumi/pulumi/issues/1660)

### To reference a tagged version

Please refer to [CHANGELOG.md](CHANGELOG.md) for the latest release.

```hcl
module "rds_uptime" {
  source = "git::https://git.zoi.de/generic/tf-modules/aws-generic-rds-uptime.git?ref=3.3.0"  
}
```

## Authors
Module managed by Graham and Emerson.

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >=3.25.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.2.0 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 3.69.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.uptime_lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.uptime_lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_log_group.rds_uptime](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_metric_filter.lambda_python_error](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_metric_filter) | resource |
| [aws_cloudwatch_metric_alarm.lambda_execution_error](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.lambda_invocation_error](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.lambda_python_error](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_iam_policy.basic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.logging](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.basic_exec](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.basic_logging](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_function.uptime](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.allow_cloudwatch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_sns_topic.alarm_rds_uptime](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | resource |
| [archive_file.function](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_account_alias"></a> [account\_alias](#input\_account\_alias) | n/a | `any` | n/a | yes |
| <a name="input_cwma_tags"></a> [cwma\_tags](#input\_cwma\_tags) | Tags for the cloud watch metric alarms | `map(string)` | `{}` | no |
| <a name="input_enable_schedule"></a> [enable\_schedule](#input\_enable\_schedule) | Defines if the function should be scheduled to run. | `bool` | `true` | no |
| <a name="input_env_mode_variable"></a> [env\_mode\_variable](#input\_env\_mode\_variable) | Enforce or set lambda to permissive | `string` | `"PERMISSIVE"` | no |
| <a name="input_env_uptime_tag_name_variable"></a> [env\_uptime\_tag\_name\_variable](#input\_env\_uptime\_tag\_name\_variable) | Uptime tag name | `string` | `"uptime"` | no |
| <a name="input_env_uptime_variables"></a> [env\_uptime\_variables](#input\_env\_uptime\_variables) | A map of the required environment variables | `map(string)` | <pre>{<br>  "UPTIME_0x7": "n-21;n-21;n-21;n-21;n-21;n-21;n-21",<br>  "UPTIME_14x5": "3-21;3-21;3-21;3-21;3-21;n-21;n-21",<br>  "UPTIME_14x6": "3-21;3-21;3-21;3-21;3-n;3-21;n-21",<br>  "UPTIME_24x5": "3-n;3-n;3-n;3-n;3-21;n-21;n-21",<br>  "UPTIME_24x6": "3-n;3-n;3-n;3-n;3-n;3-21;n-21",<br>  "UPTIME_24x7": "3-n;3-n;3-n;3-n;3-n;3-n;3-n",<br>  "UPTIME_DEFAULT": "n-n;n-n;n-n;n-n;n-n;n-n;n-n"<br>}</pre> | no |
| <a name="input_function_name"></a> [function\_name](#input\_function\_name) | The name of the function | `string` | `"svc-rds-uptime"` | no |
| <a name="input_function_role_name"></a> [function\_role\_name](#input\_function\_role\_name) | The name of the function role. | `string` | `"lambda-svc-rds-uptime"` | no |
| <a name="input_iam_role_tags"></a> [iam\_role\_tags](#input\_iam\_role\_tags) | Tags for the IAM role | `map(string)` | `{}` | no |
| <a name="input_lambda_tags"></a> [lambda\_tags](#input\_lambda\_tags) | Tags for the lambda function | `map(string)` | `{}` | no |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | `"eu-central-1"` | no |
| <a name="input_role_permissions"></a> [role\_permissions](#input\_role\_permissions) | The permissions of the function gets. | `string` | `""` | no |
| <a name="input_schedule"></a> [schedule](#input\_schedule) | When cloudwatch will trigger the function . | `string` | `"0 * * * ? *"` | no |
| <a name="input_sns_tags"></a> [sns\_tags](#input\_sns\_tags) | Tags for the SNS topic | `map(string)` | `{}` | no |
| <a name="input_timeout"></a> [timeout](#input\_timeout) | How long the lambda should run before being stopped in seconds | `string` | `"180"` | no |

## Outputs

No outputs.
