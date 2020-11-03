import os
import re
import datetime
import aws_rds_helper
import sys
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Check the enviroment variable "MODE". If undefined, assumes the default value "PERMISSIVE", which means no-changes
    # Values for MODE: PERMISSIVE or ENFORCE
    mode = os.environ.get('MODE', 'PERMISSIVE')
    regions = aws_rds_helper.load_regions()
    # If regions have been retrieved:
    if (len(regions) > 0):
        for region_name in regions:
            # look into each region and retireve RDS database instances
            print("Check region {}".format(region_name))
            rds_instances = aws_rds_helper.load_rds_instances(region_name)
            if len(rds_instances > 0):
                for instance in rds_instances:
                    # Get the DB Identifier
                    instance_id = instance["DBInstanceIdentifier"]
                    aws_rds_helper.res_log(instance_id, "Start check")
                    try:
                        # Look for the uptime tag in the instance.
                        uptime = get_uptime_details(instance, region_name)

                        # based both on the value of the uptime tag and on the lambda execution time, check if it's required to start the instance
                        start = instance_start_required(uptime)
                        aws_rds_helper.res_log(instance_id, "Start now: {type}".format(type=str(start)))

                        # based both on the value of the uptime tag and on the lambda execution time, check if it's required to stop the instance
                        stop = instance_stop_required(uptime)
                        aws_rds_helper.res_log(instance_id, "Stop now: {type}".format(type=str(stop)))

                        # Start the instance
                        if start and not stop:
                            if instance["DBInstanceStatus"] == "stopped":
                                aws_rds_helper.start_instance(instance, region_name, mode)
                                aws_helper.set_instance_msg(instance, region_name, "Instance started by uptime Tag")
                            else:
                                aws_helper.res_log(instance_id, "[WARNING] Instance {instance} found in transitional state {state}. Instance won't be started.".format(
                                    instance=instance_id, state=instance["DBInstanceStatus"]), logging.WARNING)

                        # Stop the instance
                        if stop and not start:
                            if instance["DBInstanceStatus"] == "available":
                                aws_rds_helper.stop_instance(instance, region_name, mode)
                                aws_rds_helper.set_instance_msg(instance, region_name, "Shutdown reason: Planned stop by uptime Tag")
                            else:
                                aws_helper.res_log(instance_id, "[WARNING] Instance {instance} found in transitional state {state}. Instance won't be stopped.".format(
                                    instance=instance_id, state=instance["DBInstanceStatus"]), logging.WARNING)
                        if stop and start:
                            # Invalid behaviour, log it and don't touch the instance.
                            aws_rds_helper.res_log(instance_id, "[WARNING] Has an invalid behavior, start and stop at the same time should not be the case.", logging.WARNING)
                    except:
                        aws_rds_helper.res_log(instance_id, "[ERROR] Unexpected error: {error}".format(error=sys.exc_info()[0]), logging.ERROR)
    else:
        aws_rds_helper.res_log("", "[ERROR] Could not retrieve regions. Please check credentials.", logging.ERROR)
    print("Time: "+str(datetime.datetime.now().time().hour))


def get_uptime_details(instance, region):
    has_uptime = False
    uptime_tag = os.environ.get('UPTIME_TAG', 'uptime')
    uptime_default = os.environ.get('UPTIME_DEFAULT', 'n-n;n-n;n-n;n-n;n-n;n-n;n-n')
    uptime_default = 'n-n;n-n;n-n;n-n;n-n;n-n;n-n'
    uptime_result = uptime_default
    rds_instance_tags = aws_rds_helper.get_instance_tags(instance, region)
    instance_id = instance["DBInstanceIdentifier"]
    for tag in rds_instance_tags:
        if tag.get("Key") == "uptime":
            aws_rds_helper.res_log(instance_id, "Found uptime tag")
            has_uptime = True
            uptime_orginal = tag.get("Value")
            # Check if uptime tag is set
            if uptime_orginal != None:
                aws_rds_helper.res_log(
                    instance_id, "Has explicit value: {orginal}".format(orginal=uptime_orginal))
                # Alias, are not allowed to hold ";"
                if ";" not in uptime_orginal:
                    aws_rds_helper.res_log(
                        instance_id, "Looks like an alias, try to get: UPTIME_{orginal}".format(orginal=uptime_orginal))
                    aws_rds_helper.res_log(
                        instance_id, "Has explicit value: {orginal}".format(orginal=uptime_orginal))
                    # try to get from env
                    if ('UPTIME_'+uptime_orginal) in os.environ:
                        uptime_result = os.environ['UPTIME_'+uptime_orginal]
                        aws_rds_helper.res_log(instance_id, "Found Alias with value: {value}".format(value=uptime_result))
                    else:
                        aws_rds_helper.res_log(instance_id, "[INFO] No alias found for: {orginal} (use default)".format(orginal=uptime_orginal))
                else:
                    aws_rds_helper.res_log(instance_id, "[INFO] Use explicit value: {orginal}".format(orginal=uptime_orginal))
                    uptime_result = uptime_orginal
            else:
                aws_rds_helper.res_log(instance_id, "[INFO] No Tag {tag} found, use default: {default}".format(tag=uptime_tag, default=uptime_default))
    if not has_uptime:
        aws_rds_helper.res_log(instance_id, "[INFO] No tags found at all, use default: {default}".format(default=uptime_default))
    # validate value
    re_pattern = re.compile(r'([0-9|n]{1,2}\-[0-9|n]{1,2};?){7}')
    if (re_pattern.match(uptime_result) == None):
        aws_rds_helper.res_log(instance_id, "[INFO] Uptime looks invalid, reset to default")
        uptime_result = uptime_default
    return transform_uptime(uptime_result)


def transform_uptime(uptime):
    result = []
    splitted_uptime = uptime.split(";")
    for up in splitted_uptime:
        splitted_day_update = up.split("-")
        result.append({"start": splitted_day_update[0], "stop": splitted_day_update[1]})
    return result


def instance_stop_required(uptime):
    now = datetime.datetime.utcnow()
    today_start_stop = uptime[now.weekday()]
    if today_start_stop["stop"] == str(now.time().hour):
        return True
    else:
        return False


def instance_start_required(uptime):
    now = datetime.datetime.utcnow()
    today_start_stop = uptime[now.weekday()]
    if today_start_stop["start"] == str(now.time().hour):
        return True
    else:
        return False
