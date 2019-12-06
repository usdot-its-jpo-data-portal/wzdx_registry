"""
Helper class for interacting with datasets in Socrata.

"""
import boto3
import copy
import itertools
import json
import os
import requests
from sodapy import Socrata
import time


class SocrataDataset(object):
    """
    Helper class for interacting with datasets in Socrata.

    """
    def __init__(self, dataset_id, socrata_client=None, socrata_params={}, float_fields=[], logger=None):
        """
        Initialization function of the SocrataDataset class.

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
        """
        self.dataset_id = dataset_id
        self.client = socrata_client
        if not socrata_client and socrata_params:
            self.client = Socrata(**socrata_params)
        self.socrata_params = socrata_params
        self.col_dtype_dict = self.get_col_dtype_dict()
        self.float_fields = float_fields
        self.print_func = print
        if logger:
            self.print_func = logger.info

    def get_col_dtype_dict(self):
        """
        Retrieve data dictionary of a Socrata data set in the form of a dictionary,
        with the key being the column name and the value being the column data type

    	Returns:
    		Data dictionary of a Socrata data set in the form of a dictionary,
            with the key being the column name and the value being the column data type.
        """
        dataset_col_meta = self.client.get_metadata(self.dataset_id)['columns']
        col_dtype_dict = {col['name']: col['dataTypeName'] for col in dataset_col_meta}
        return col_dtype_dict

    def mod_dtype(self, rec, col_dtype_dict=None, float_fields=None):
        """
        Make sure the data type of each field in the data record matches the data type
        of the field in the Socrata data set.

    	Parameters:
    		rec: dictionary object of the data record
            col_dtype_dict: data dictionary of a Socrata data set in the form of a dictionary,
            with the key being the column name and the value being the column data type
            float_fields: list of fields that should be a float

    	Returns:
    		Dictionary object of the data record, with number, string, and boolean fields
            modified to align with the data type of the corresponding Socrata data set.
        """
        col_dtype_dict = col_dtype_dict or self.col_dtype_dict
        float_fields = float_fields or self.float_fields

        identity = lambda x: x
        dtype_func = {'number': float, 'text': str, 'checkbox': bool}
        out = {}
        for k,v in rec.items():
            if k in float_fields and k in col_dtype_dict:
                out[k] = float(v)
            elif k in col_dtype_dict:
                if v not in [None, '']:
                    out[k] = dtype_func.get(col_dtype_dict.get(k, 'nonexistentKey'), identity)(v)
        out = {k:v for k,v in out.items() if k in col_dtype_dict}
        return out

    def create_new_draft(self):
        """
        Create a new draft of the current dataset.

        Returns:
            Draft ID of the new draft.
        """
        draftDataset = requests.post('https://{}/api/views/{}/publication.json'.format(self.client.domain, self.dataset_id),
                                  auth=(self.socrata_params['username'], self.socrata_params['password']),
                                  params={'method': 'copySchema'})
        logger.info(draftDataset.json())
        draftId = draftDataset.json()['id']
        return draftId

    def publish_draft(self, draftId):
        """
        Publish the Socrata draft specified.

        Parameters:
            draftId: 4x4 ID of the Socrata draft (e.g. x123-bc12)

        Returns:
            Response of the publish draft request.
        """
        time.sleep(5)
        publishResponse = requests.post('https://{}/api/views/{}/publication.json'.format(self.client.domain, draftId),
                                        auth=(self.socrata_params['username'], self.socrata_params['password']))
        logger.info(publishResponse.json())
        return publishResponse

    def delete_draft(self, draftId):
        """
        Delete the Socrata draft specified.

        Parameters:
            draftId: 4x4 ID of the Socrata draft (e.g. x123-bc12)

        Returns:
            Response of the delete draft request.
        """
        time.sleep(5)
        deleteResponse = self.client.delete(draftId)
        if deleteResponse.status_code == 200:
            logger.info('Empty draft {} has been discarded.'.format(draftId))
        return deleteResponse

    def clean_and_upsert(self, recs, dataset_id=None):
        """
        Publish the Socrata draft specified.

        Parameters:
            recs: an array of dictionary objects of the data to upsert.
            dataset_id: 4x4 ID of the Socrata dataset (e.g. x123-bc12) to perform
            upserts to. This parameter is not required if you are performing upserts to the
            dataset you've initialized this class with.

        Returns:
            A dictionary object with the following fields:
            'Rows Deleted' - number of rows deleted due to the upsert request
            'Rows Updated' - number of rows updated due to the upsert request
            'Rows Created' - number of rows created due to the upsert request
        """
        dataset_id = dataset_id or self.dataset_id
        out_recs = [self.mod_dtype(r) for r in recs]
        uploadResponse = self.client.upsert(dataset_id, out_recs)
        return uploadResponse
