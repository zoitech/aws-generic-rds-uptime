import boto3
from boto3.session import Session
import os
import re
import logging
logger = logging.getLogger()

def load_regions():
    """Returns a list of all regions.

        Params:
            -   
        Returns: list
    """
    try:
        s = Session()
        regions = s.get_available_regions('rds')
        return regions
    except :
        print("[ERROR] Fetching regions, fallback to empty list.",logging.ERROR)
        return []

def load_rds_instances(region):
    """Returns a list of all RDS instances in the given region.
    
    Params: 
        region   (String) : AWS region alias 

    Returns: list
    """
    try:
        rds = boto3.client('rds',region)
        instances = []
        paginator = rds.get_paginator("describe_db_instances")
        pages = paginator.paginate()
        for page in pages:
            for instance in page["DBInstances"]:
                    instances.append(instance)
        return instances
    except:
        print("[INFO] Fetching rds instances in the region {region}.".format(region=region),logging.INFO)
        return []

def start_instance(instance,region,mode):
    """Starts an RDS instance, if mode equals to 'ENFORCE'
    
        Params: 
            instance (dict)   : RDS instance object.
            region   (String) : AWS region alias 
            mode     (String) : [ENFORCE | PERMISSIVE]
    """
    instance_id = instance["DBInstanceIdentifier"]
    if instance["DBInstanceStatus"] == "stopped":
        if(mode == "ENFORCE"):
            res_log(instance_id,"Starting")
            rds = boto3.client('rds',region)
            rds.start_db_instance(DBInstanceIdentifier=instance_id)
        else:
             res_log(instance_id,"Starting - SKIPPED as not in ENFORCE mode")
    else:
        res_log(instance_id,"Starting - SKIPPED due to state {state}".format(state=instance["DBInstanceStatus"]))

def stop_instance(instance,region,mode):
    """Stops an instance, if mode equals to 'ENFORCE'

        Params: 
            instance (dict)   : RDS instance object.
            region   (String) : AWS region alias 
            mode     (String) : [ENFORCE | PERMISSIVE]
        
    """
    instance_id = instance["DBInstanceIdentifier"]
    if instance["DBInstanceStatus"] == "available":
        if(mode == "ENFORCE"):
            res_log(instance_id,"Stopping")
            rds = boto3.client('rds',region)
            rds.stop_db_instance(DBInstanceIdentifier=instance_id)
        else:
            res_log(instance_id,"Stopping - SKIPPED as not in ENFORCE mode")
    else:
        res_log(instance_id,"Stopping - SKIPPED due to state {state}".format(state=instance["DBInstanceStatus"]))

def set_instance_msg(instance,region,message):
    """Add a 'Meessage' tag with the value of message to the give instance.
        
        Params: 
            instance (dict)   : RDS instance object.
            region   (String) : AWS region alias 
            message  (String) : A message to be written
    """
    set_rds_tag(res_id=instance["DBInstanceArn"],region=region,key="Message",value=message)

def set_rds_tag(res_id, region, key, value):
    """Add a 'Message' tag with the value of message to the given resource.

        Params: 
            res_id  (String) : RDS instance ARN.
            region  (String) : AWS region alias 
            key     (String) : Key name
            message (String) : A message to be written
    """
    res_log(res_id,"Set {key} to {value}".format(key=key,value=value))
    rds = boto3.client('rds',region)
    print("Set {key} to {value}".format(key=key,value=value))
    rds.add_tags_to_resource(ResourceName=res_id,Tags=[{"Key":key,"Value":value}])

def get_instance_tags(instance,region):
    """Returns the tags from a given list of instances where the instance id equals to DBInstanceIdentifier. If not found an empty array is returned.
        
        Params: 
            instance (dict)   : RDS instance object.
            region   (String) : AWS region alias 

        Returns: list
    """
    rds = boto3.client('rds',region)
    return rds.list_tags_for_resource(ResourceName=instance["DBInstanceArn"])["TagList"]

def get_configTag_value(tags,keyname):
    """Returns the value a Key keyname of a Key/Value map. If not found the value is None
    This function is for AWS config where key/value are written lowerCase other then on the rest of the APIs.

        Params:     
            tags (dict)      : All Tags from Instance
            keyname (String) : Name of a required Tag
        
        Returns: String
    """
    if keyname in tags:
        return tags[keyname]
    return None

def res_log(id,message,lvl=logging.INFO):
    """Log a message with id as prefix.
    
        Params:     
            id      (String) : Instance name
            message (String) : Log message
            lvl     (Object) : Log level
    """
    full_message="{id}\t{message}".format(id=id,message=message)
    logger.log(lvl, full_message)