"""
Lambda function that triggers a separate ingestion lambda function based on the WZDx Feed Registry Socrata dataset.

"""
from __future__ import print_function

import json
import logging
import os
import traceback

from wzdx_registry import WZDxFeedRegistry


logger = logging.getLogger()
logger.setLevel(logging.INFO)  # necessary to make sure aws is logging


DATASET_ID = os.environ.get('DATASET_ID')
LAMBDA_TO_TRIGGER = os.environ.get('LAMBDA_TO_TRIGGER')
SOCRATA_PARAMS = os.environ.get('SOCRATA_PARAMS')

if None in [DATASET_ID, LAMBDA_TO_TRIGGER, SOCRATA_PARAMS]:
    logger.error('Required ENV variable(s) not found. Please make sure you have specified the following ENV variables: DATASET_ID, LAMBDA_TO_TRIGGER, SOCRATA_PARAMS')
    exit()


def lambda_handler(event=None, context=None):
    """
    AWS Lambda handler.

    """
    wzdx_registry = WZDxFeedRegistry(DATASET_ID,
                                    socrata_params=json.loads(SOCRATA_PARAMS),
                                    lambda_to_trigger=LAMBDA_TO_TRIGGER,
                                    logger=logger)
    wzdx_registry.ingest()


if __name__ == '__main__':
    lambda_handler()
