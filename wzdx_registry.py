'''
Class for triggering ingestion lambda functions when needed based on WZDx Feed Registry Scorata dataset.

'''
from copy import deepcopy
from datetime import datetime, timedelta
import dateutil.parser
import json
import requests
import re

from socrata_util import SocrataDataset
from s3_helper import AWS_helper


class WZDxFeedRegistry(SocrataDataset):
    def __init__(self, dataset_id, lambda_to_trigger=None, aws_profile=None, **kwargs):
        super(WZDxFeedRegistry, self).__init__(dataset_id, **kwargs)
        self.lambda_to_trigger=lambda_to_trigger
        self.aws = AWS_helper(aws_profile)

    def get_active_feeds(self):
        data = self.client.get(self.dataset_id, where='active = true', exclude_system_fields=False)
        return data

    def get_next_ingest_time(self, update_freq, last_ingest_time):
        time_unit_dict = {'h': 'hours', 'm': 'minutes', 's': 'seconds'}

        time_regex = r'(\d+)(\w+)'
        time_num, time_unit = re.findall(time_regex, update_freq)[0]
        time_num = int(time_num)
        time_unit = time_unit_dict[time_unit]
        next_ingest_time = dateutil.parser.parse(last_ingest_time) + timedelta(**{time_unit: time_num})
        return next_ingest_time

    def trigger_lambda_ingestion(self, feed):
        self.print_func('Trigger {} for {}'.format(self.lambda_to_trigger, feed['feedname']))
        # invoke lambda asynchronously
        data_to_send = {'feed': feed, 'dataset_id': self.dataset_id}
        lambda_client = self.aws.session.client('lambda')
        response = lambda_client.invoke(
            FunctionName=self.lambda_to_trigger,
            InvocationType='Event',
            LogType='Tail',
            ClientContext='',
            Payload=json.dumps(data_to_send).encode('utf-8'),
        )
        self.print_func(response)

        # update last ingest time
        feed['lastingestedtosandbox'] = datetime.now().isoformat()
        response = self.client.upsert(self.dataset_id, [feed])
        self.print_func(response)

    def check_feed(self, feed):
        update_freq = feed.get('datafeed_frequency_update')
        last_ingest_time = feed.get('lastingestedtosandbox')
        if not last_ingest_time:
            self.trigger_lambda_ingestion(feed)
        else:
            next_ingest_time = self.get_next_ingest_time(update_freq, last_ingest_time)
            if datetime.now() > next_ingest_time:
                self.trigger_lambda_ingestion(feed)
            else:
                self.print_func('Skip {}'.format(feed['feedname']))

    def ingest(self):
        feeds = self.get_active_feeds()
        for feed in feeds:
            self.check_feed(feed)
