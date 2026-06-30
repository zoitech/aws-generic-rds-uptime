import start_stop_rds as start_stop
import unittest
import datetime
import json
import os
import logging
from unittest.mock import patch, MagicMock

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class test_transform_uptime(unittest.TestCase):
    def test_hasRightLength(self):
        result = start_stop.transform_uptime(
            '8-22;8-22;8-22;8-22;8-22;n-0;n-0')
        self.assertEqual(len(result), 7)

    def test_hasRightValue(self):
        result = start_stop.transform_uptime(
            '8-22;8-22;8-22;8-22;8-22;n-0;n-0')
        self.assertEqual(result[6]['start'], 'n')


class test_instance_stop_required(unittest.TestCase):
    def setUp(self):
        now = datetime.datetime.utcnow()
        self.dummy_positive_uptime = start_stop.transform_uptime(
            '8-22;8-22;8-22;8-22;8-22;n-0;n-0')
        self.dummy_positive_uptime[now.weekday()]['start'] = str(
            now.time().hour)
        self.dummy_positive_uptime[now.weekday()]['stop'] = str(
            now.time().hour)
        self.dummy_positive_negative = start_stop.transform_uptime(
            'n-n;n-n;n-n;n-n;n-n;n-n;n-n')

    def test_positiveStop(self):
        result = start_stop.instance_stop_required(self.dummy_positive_uptime)
        self.assertTrue(result)

    def test_positiveStart(self):
        result = start_stop.instance_start_required(self.dummy_positive_uptime)
        self.assertTrue(result)

    def test_negativeStop(self):
        result = start_stop.instance_stop_required(
            self.dummy_positive_negative)
        self.assertFalse(result)

    def test_negativeStart(self):
        result = start_stop.instance_start_required(
            self.dummy_positive_negative)
        self.assertFalse(result)


class test_get_uptime_details(unittest.TestCase):
    region = "eu-central-1"

    def setUp(self):
        self.dummy_instance = {
            "DBInstanceIdentifier": "test-rds-1",
            "DBInstanceArn": "arn:aws:rds:eu-central-1:123456789012:db:test-rds-1"
        }
        os.environ["UPTIME_24x5"] = "n-n;n-n;n-n;n-n;n-n;n-n;1-n"

    @patch('start_stop_rds.aws_rds_helper.get_instance_tags')
    def test_full(self, mock_get_tags):
        mock_get_tags.return_value = [
            {"Key": "Name", "Value": "test-rds-1"},
            {"Key": "uptime", "Value": "n-n;n-n;n-n;n-n;n-n;n-n;n-n"}
        ]
        result = start_stop.get_uptime_details(self.dummy_instance, self.region)
        self.assertEqual(result[6]['start'], 'n')

    @patch('start_stop_rds.aws_rds_helper.get_instance_tags')
    def test_alias(self, mock_get_tags):
        mock_get_tags.return_value = [
            {"Key": "Name", "Value": "test-rds-1"},
            {"Key": "uptime", "Value": "24x5"}
        ]
        result = start_stop.get_uptime_details(self.dummy_instance, self.region)
        self.assertEqual(result[6]['start'], '1')

    @patch('start_stop_rds.aws_rds_helper.get_instance_tags')
    def test_none(self, mock_get_tags):
        mock_get_tags.return_value = [
            {"Key": "Name", "Value": "test-rds-1"}
        ]
        result = start_stop.get_uptime_details(self.dummy_instance, self.region)
        self.assertEqual(result[6]['stop'], 'n')

    @patch('start_stop_rds.aws_rds_helper.get_instance_tags')
    def test_invalid1(self, mock_get_tags):
        mock_get_tags.return_value = [
            {"Key": "Name", "Value": "test-rds-1"},
            {"Key": "uptime", "Value": "n-n;n-n;n-n;n-n;n-n;n-n;n-"}
        ]
        result = start_stop.get_uptime_details(self.dummy_instance, self.region)
        self.assertEqual(result[6]['stop'], 'n')

    @patch('start_stop_rds.aws_rds_helper.get_instance_tags')
    def test_invalid2(self, mock_get_tags):
        mock_get_tags.return_value = [
            {"Key": "Name", "Value": "test-rds-1"},
            {"Key": "uptime", "Value": "n-n;n-n;n-n;n-n;n-"}
        ]
        result = start_stop.get_uptime_details(self.dummy_instance, self.region)
        self.assertEqual(result[6]['stop'], 'n')


class test_lambda_handler_logging(unittest.TestCase):
    @patch('start_stop_rds.aws_rds_helper.load_regions')
    @patch('start_stop_rds.logger')
    def test_lambda_handler_logs_error_when_no_regions(self, mock_logger, mock_load_regions):
        """lambda_handler() should call logger.error (not print) when no regions are found."""
        mock_load_regions.return_value = []
        start_stop.lambda_handler({}, None)
        mock_logger.error.assert_called_once_with("Could not retrieve regions. Please check credentials.")

    @patch('start_stop_rds.aws_rds_helper.load_regions')
    @patch('builtins.print')
    def test_lambda_handler_does_not_use_print(self, mock_print, mock_load_regions):
        """lambda_handler() should NOT use print for error output."""
        mock_load_regions.return_value = []
        start_stop.lambda_handler({}, None)
        mock_print.assert_not_called()


if __name__ == '__main__':
    unittest.main()
