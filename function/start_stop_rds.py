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
    if len(regions) > 0:
        for region_name in regions:
            # look into each region and retireve RDS database instances
            logger.info("Check region {}".format(region_name))
            rds_instances = aws_rds_helper.load_rds_instances(region_name)
            if len(rds_instances) > 0:
                for instance in rds_instances:
                    # Get the DB Identifier
                    instance_id = instance["DBInstanceIdentifier"]
                    logger.info("{}: Start check".format(instance_id))
                    try:
                        # Look for the uptime tag in the instance.
                        uptime = get_uptime_details(instance, region_name)

                        # based both on the value of the uptime tag and on the lambda execution time, check if it's required to start the instance
                        start = instance_start_required(uptime)
                        logger.info("{}: Start now: {}".format(instance_id, str(start)))

                        # based both on the value of the uptime tag and on the lambda execution time, check if it's required to stop the instance
                        stop = instance_stop_required(uptime)
                        logger.info("{}: Stop now: {}".format(instance_id, str(stop)))

                        # Start the instance
                        if start and not stop:
                            if instance["DBInstanceStatus"] == "stopped":
                                aws_rds_helper.start_instance(instance, region_name, mode)
                                aws_rds_helper.set_instance_msg(instance, region_name, "Instance started by uptime Tag")
                            else:
                                logger.warning("{}: Instance {} found in transitional state {}. Instance won't be started.".format(
                                    instance_id, instance_id, instance["DBInstanceStatus"]))

                        # Stop the instance
                        if stop and not start:
                            if instance["DBInstanceStatus"] == "available":
                                aws_rds_helper.stop_instance(instance, region_name, mode)
                                aws_rds_helper.set_instance_msg(instance, region_name, "Shutdown reason: Planned stop by uptime Tag")
                            else:
                                logger.warning("{}: Instance {} found in transitional state {}. Instance won't be stopped.".format(
                                    instance_id, instance_id, instance["DBInstanceStatus"]))
                        if stop and start:
                            # Invalid behaviour, log it and don't touch the instance.
                            logger.warning("{}: Has an invalid behavior, start and stop at the same time should not be the case.".format(instance_id))
                    except:
                        logger.error("{}: Unexpected error: {}".format(instance_id, sys.exc_info()[0]))
    else:
        logger.error("Could not retrieve regions. Please check credentials.")
    logger.info("Time: "+str(datetime.datetime.now().time().hour))


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
            logger.info("{}: Found uptime tag".format(instance_id))
            has_uptime = True
            uptime_orginal = tag.get("Value")
            # Check if uptime tag is set
            if uptime_orginal != None:
                logger.info("{}: Has explicit value: {}".format(instance_id, uptime_orginal))
                # Alias, are not allowed to hold ";"
                if ";" not in uptime_orginal:
                    logger.info("{}: Looks like an alias, try to get: UPTIME_{}".format(instance_id, uptime_orginal))
                    logger.info("{}: Has explicit value: {}".format(instance_id, uptime_orginal))
                    # try to get from env
                    if ('UPTIME_'+uptime_orginal) in os.environ:
                        uptime_result = os.environ['UPTIME_'+uptime_orginal]
                        logger.info("{}: Found Alias with value: {}".format(instance_id, uptime_result))
                    else:
                        logger.info("{}: No alias found for: {} (use default)".format(instance_id, uptime_orginal))
                else:
                    logger.info("{}: Use explicit value: {}".format(instance_id, uptime_orginal))
                    uptime_result = uptime_orginal
            else:
                logger.info("{}: No Tag {} found, use default: {}".format(instance_id, uptime_tag, uptime_default))
    if not has_uptime:
        logger.info("{}: No tags found at all, use default: {}".format(instance_id, uptime_default))
    # validate value
    re_pattern = re.compile(r'([0-9|n]{1,2}\-[0-9|n]{1,2};?){7}')
    if (re_pattern.match(uptime_result) == None):
        logger.info("{}: Uptime looks invalid, reset to default".format(instance_id))
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
