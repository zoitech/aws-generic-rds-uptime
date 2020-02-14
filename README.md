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

The module requires no inputs to run:

```hcl
module "rds_uptime" {
  source = "git::https://git.zoi.de/terraform-library/aws-generic-rds-uptime.git"
```

However it is possible to amend most variables such as schedule, names etc if desired:

```hcl
module "rds_uptime" {
  source = "git::https://github.com/zoitech/terraform-aws-rds-uptime.git"
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

By default the variable "env_mode_variable" is set to "ENFORCE". This can also be set to "PERMISSIVE", which will prevent the lambda function from starting or stopping all RDS instances.

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

### To reference a tagged version

Please refer to [CHANGELOG.md](CHANGELOG.md) for the latest release.

```hcl
module "iam_saml" {
  source = "git::https://github.com/zoitech/terraform-aws-rds-uptime.git?ref=1.0.0"  
}
```

## Authors
Module managed by [Zoi](https://github.com/zoitech).

## License
MIT License. See LICENSE for full details.