"""
Class for triggering ingestion lambda functions when needed based on WZDx Feed Registry Scorata dataset.

"""
from copy import deepcopy
from datetime import datetime, timedelta
import dateutil.parser
import json
import requests
import re

from socrata_util import SocrataDataset
from s3_helper import AWS_helper


class WZDxFeedRegistry(SocrataDataset):
    """
    Class to interact with the WZDx Feed Registry Socrata Dataset.

    """
    def __init__(self, dataset_id, lambda_to_trigger=None, aws_profile=None, **kwargs):
        """
        Initialization function of the WZDxFeedRegistry class.

        Parameters:
            dataset_id: 4x4 ID of the Socrata draft (e.g. x123-bc12)
            client: Optional parameter if the user chooses to pass in the
                socrata_params parameter. If user chooses not to pass in
                socrata_params, they can also pass in an sodapy.Socrata object
                that has been initialized with the proper socrata credentials.
            socrata_params: Optional parameter if the user choose to pass in the
                socrata_client parameter. Dictionary object containing Socrata
                credentials. Must include the following fields: 'username',
                'password', 'app_token', 'domain'.
            float_fields: An array of Socrata field names that should be of
                float types (numbers with decimals).
            logger: Optional parameter. Could pass in a logger object or not pass
                in anything. If a logger object is passed in, information will be
                logged instead of printed. If not, information will be printed.
            lambda_to_trigger: Name of the feed ingestion lambda function you'd like
                to invoke.
            aws_profile: Optional string name of your AWS profile, as set up in
                the credential file at ~/.aws/credentials. No need to pass in
                this parameter if you will be using your default profile. For
                additional information on how to set up the credential file, see
                https://docs.aws.amazon.com/sdk-for-php/v3/developer-guide/guide_credentials_profiles.html
        """
        super(WZDxFeedRegistry, self).__init__(dataset_id, **kwargs)
        self.lambda_to_trigger=lambda_to_trigger
        self.aws = AWS_helper(aws_profile)

        self.n_ingest_triggered = 0

    def get_active_feeds(self):
        """
        Method for getting all active feeds from the feed registry.

        Returns:
            An array of dictionary objects with each object being a row (feed)
            in the feed registry where `active`=true
        """
        data = self.client.get(self.dataset_id, where='active = true', exclude_system_fields=False)
        return data

    def get_next_ingest_time(self, update_freq, last_ingest_time):
        """
        Method for getting next ingestion time based on a feed's last ingested
        time and update frequency.

        Parameters:
            update_freq: string representation of the update frequency of a feed.
                This is taken from the `datafeed_frequency_update` field of the
                feed registry record and is in the format of concatenated number
                followed by h/m/s for hours/minutes/seconds. E.g. values of '12h',
                '5m', or '30s' means the feed is updated once every 12 hours,
                once every 30 minutes, or once every 30 seconds, respectively.
            last_ingest_time: ISO formatted string of last ingested time in UTC.

        Returns:
            Datetime object for next ingestion time.
        """
        time_unit_dict = {'h': 'hours', 'm': 'minutes', 's': 'seconds'}

        time_regex = r'(\d+)(\w+)'
        time_num, time_unit = re.findall(time_regex, update_freq)[0]
        time_num = int(time_num)
        time_unit = time_unit_dict[time_unit]
        next_ingest_time = dateutil.parser.parse(last_ingest_time) + timedelta(**{time_unit: time_num})
        return next_ingest_time

    def trigger_lambda_ingestion(self, feed):
        """
        Method to trigger an ingestion lambda function on a particular feed. The
        "last ingested to sandbox" field for the feed's record in the WZDx Feed
        Registry will be updated to the current UTC timestamp.

        Parameters:
            feed: dictionary object. Should be a record read from the WZDx feed
                registry Socrata dataset, with all fields, including the system
                fields (e.g. ':id').
        """
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
        self.n_ingest_triggered += 1

    def check_feed(self, feed):
        """
        Method to check if the ingestion lambda should be triggered for a feed
        based on its last ingest time and update frequency.

        Parameters:
            feed: dictionary object. Should be a record read from the WZDx feed
                registry Socrata dataset, with all fields, including the system
                fields (e.g. ':id').
        """
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
        """
        Method to retrieve all active feeds from the WZDx Feed Registry and trigger
        ingestion for each feed based on its last ingest time and update frequency.

        """
        feeds = self.get_active_feeds()
        self.print_func('{} active feeds found in Socrata Feed Registry at http://{}/d/{}.'.format(len(feeds), self.socrata_params['domain'], self.dataset_id))

        for feed in feeds:
            self.check_feed(feed)
        self.print_func('{} ingestion triggered.'.format(self.n_ingest_triggered))
