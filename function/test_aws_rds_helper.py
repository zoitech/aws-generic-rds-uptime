from moto import mock_aws
import aws_rds_helper
import unittest
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Helper config
region = "eu-central-1"


@mock_aws
class test_load_regions(unittest.TestCase):
    def test_hasLen(self):
        result = aws_rds_helper.load_regions()
        # moto returns standard mock regions, checking that it's a list with regions
        self.assertGreater(len(result), 0)
        self.assertIn("eu-central-1", result)


@mock_aws
class test_load_rds_instances(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('rds', region)
        self.client.create_db_instance(
            DBInstanceIdentifier='test-rds-1',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            AllocatedStorage=20,
            MasterUsername='username',
            MasterUserPassword='password'
        )

    def test_hasLen(self):
        result = aws_rds_helper.load_rds_instances(region)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["DBInstanceIdentifier"], 'test-rds-1')


@mock_aws
class test_start_instance(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('rds', region)
        self.client.create_db_instance(
            DBInstanceIdentifier='test-rds-start',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            AllocatedStorage=20,
            MasterUsername='username',
            MasterUserPassword='password'
        )
        try:
            self.client.stop_db_instance(DBInstanceIdentifier='test-rds-start')
        except Exception:
            pass

    def test_start_enforce(self):
        instance = {"DBInstanceIdentifier": "test-rds-start", "DBInstanceStatus": "stopped"}
        aws_rds_helper.start_instance(instance, region, "ENFORCE")
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-start')
        self.assertIn(db_desc['DBInstances'][0]['DBInstanceStatus'], ['starting', 'available'])

    def test_start_permissive(self):
        instance = {"DBInstanceIdentifier": "test-rds-start", "DBInstanceStatus": "stopped"}
        aws_rds_helper.start_instance(instance, region, "PERMISSIVE")
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-start')
        self.assertEqual(db_desc['DBInstances'][0]['DBInstanceStatus'], 'stopped')


@mock_aws
class test_stop_instance(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('rds', region)
        self.client.create_db_instance(
            DBInstanceIdentifier='test-rds-stop',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            AllocatedStorage=20,
            MasterUsername='username',
            MasterUserPassword='password'
        )

    def test_stop_enforce(self):
        instance = {"DBInstanceIdentifier": "test-rds-stop", "DBInstanceStatus": "available"}
        aws_rds_helper.stop_instance(instance, region, "ENFORCE")
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-stop')
        self.assertIn(db_desc['DBInstances'][0]['DBInstanceStatus'], ['stopping', 'stopped'])

    def test_stop_permissive(self):
        instance = {"DBInstanceIdentifier": "test-rds-stop", "DBInstanceStatus": "available"}
        aws_rds_helper.stop_instance(instance, region, "PERMISSIVE")
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-stop')
        self.assertEqual(db_desc['DBInstances'][0]['DBInstanceStatus'], 'available')


@mock_aws
class test_set_instance_msg(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('rds', region)
        self.client.create_db_instance(
            DBInstanceIdentifier='test-rds-tag',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            AllocatedStorage=20,
            MasterUsername='username',
            MasterUserPassword='password'
        )
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-tag')
        self.db_arn = db_desc['DBInstances'][0]['DBInstanceArn']

    def test_set_msg(self):
        instance = {"DBInstanceIdentifier": "test-rds-tag", "DBInstanceArn": self.db_arn}
        aws_rds_helper.set_instance_msg(instance, region, "test-message")
        
        tags_response = self.client.list_tags_for_resource(ResourceName=self.db_arn)
        tags = tags_response.get("TagList", [])
        
        message_tag = next((tag for tag in tags if tag["Key"] == "Message"), None)
        self.assertIsNotNone(message_tag)
        self.assertEqual(message_tag["Value"], "test-message")


@mock_aws
class test_get_instance_tags(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('rds', region)
        self.client.create_db_instance(
            DBInstanceIdentifier='test-rds-get-tags',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            AllocatedStorage=20,
            MasterUsername='username',
            MasterUserPassword='password',
            Tags=[
                {"Key": "uptime", "Value": "24x7"},
                {"Key": "Environment", "Value": "Production"}
            ]
        )
        db_desc = self.client.describe_db_instances(DBInstanceIdentifier='test-rds-get-tags')
        self.db_arn = db_desc['DBInstances'][0]['DBInstanceArn']

    def test_get_tags(self):
        instance = {"DBInstanceIdentifier": "test-rds-get-tags", "DBInstanceArn": self.db_arn}
        result = aws_rds_helper.get_instance_tags(instance, region)
        
        uptime_tag = next((tag for tag in result if tag["Key"] == "uptime"), None)
        self.assertIsNotNone(uptime_tag)
        self.assertEqual(uptime_tag["Value"], "24x7")


# --- Logging behavior tests ---
from unittest.mock import patch, MagicMock


class test_load_regions_logging(unittest.TestCase):
    @patch('aws_rds_helper.Session', side_effect=Exception("connection error"))
    @patch('aws_rds_helper.logger')
    def test_logs_error_on_exception(self, mock_logger, mock_session):
        """load_regions() should call logger.error (not print) when an exception occurs."""
        result = aws_rds_helper.load_regions()
        self.assertEqual(result, [])
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn("Fetching regions", call_args)

    @patch('aws_rds_helper.Session', side_effect=Exception("connection error"))
    @patch('builtins.print')
    def test_does_not_use_print(self, mock_print, mock_session):
        """load_regions() should NOT use print for error output."""
        aws_rds_helper.load_regions()
        mock_print.assert_not_called()


class test_load_rds_instances_logging(unittest.TestCase):
    @patch('aws_rds_helper.boto3.client', side_effect=Exception("access denied"))
    @patch('aws_rds_helper.logger')
    def test_logs_info_on_exception(self, mock_logger, mock_client):
        """load_rds_instances() should call logger.info (not print) when an exception occurs."""
        result = aws_rds_helper.load_rds_instances(region)
        self.assertEqual(result, [])
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0]
        self.assertIn(region, call_args)

    @patch('aws_rds_helper.boto3.client', side_effect=Exception("access denied"))
    @patch('builtins.print')
    def test_does_not_use_print(self, mock_print, mock_client):
        """load_rds_instances() should NOT use print for error output."""
        aws_rds_helper.load_rds_instances(region)
        mock_print.assert_not_called()


if __name__ == '__main__':
    unittest.main()
