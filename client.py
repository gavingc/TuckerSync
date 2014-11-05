"""Tucker Sync client module.

Usage:
    from client import Client
    client = Client(base_url)
    client.check_connection()

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout
"""

import requests
import uuid

from common import APIQuery, JSONKey, APIErrorCode, HTTP, JSON, Logger

LOG = Logger(__file__)


class Client(object):

    """A Tucker Sync Client Implementation."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.UUID = uuid.uuid4()
        # TODO init storage.

    def check_connection(self):
        url = self.base_url + APIQuery.TEST
        response = requests.post(url)

        LOG.debug(self, 'url = %s', url)

        try:
            jo = self.get_json_object(response)
        except Exception as e:
            LOG.debug(self, 'Check connection failed with exception = %s', e)
            return False

        if jo[JSONKey.ERROR] != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Check connection failed with API error code = %s', jo[JSONKey.ERROR])
            return False

        # Success
        return True

    @staticmethod
    def get_json_object(response):
        """Get the json object (Python dictionary) from the response or raise an exception."""

        LOG.debug(Client, 'status_code = %s', response.status_code)
        LOG.debug(Client, 'content = %s', response.content)

        if response.status_code != HTTP.OK:
            LOG.debug(Client, 'HTTP status code != HTTP.OK')
            raise Exception

        try:
            jo = JSON.loads(response.content)
        except Exception as e:
            LOG.debug(Client, 'get_json_object exception = %s', e)
            raise e

        if not type(jo) is dict:
            LOG.debug(Client, 'Type of jo is not an object/dict.')
            raise Exception

        if not JSONKey.ERROR in jo:
            LOG.debug(Client, 'The decoded jo has no `error` key.')
            raise Exception

        # Success.
        return jo
