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

    def __init__(self, base_url, key, email, password):
        self.base_url = base_url
        self.key = key
        self.email = email
        self.password = password
        self.UUID = uuid.uuid4()
        # TODO init storage.

    def check_connection(self):
        """Check the connection to the server and that it responds with an API error code."""
        try:
            self.post_request(APIQuery.TEST)
        except ClientException:
            LOG.debug(self, 'Check connection failed with an exception.')
            return False

        # Success
        return True

    def check_authentication(self):
        """Check that authentication against an account on the server succeeds."""
        try:
            jo = self.post_request(APIQuery.TEST)
        except ClientException:
            LOG.debug(self, 'Check authentication failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Check authentication failed with API error code = %s', error_code)
            return False

        # Success
        return True

    def account_open(self):
        """Open a new account on the server."""
        try:
            jo = self.post_request(APIQuery.ACCOUNT_OPEN)
        except ClientException:
            LOG.debug(self, 'Account open failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account open failed with API error code = %s', error_code)
            return False

        # Success
        return True

    def account_close(self):
        """Close an existing account on the server."""
        try:
            jo = self.post_request(APIQuery.ACCOUNT_CLOSE)
        except ClientException:
            LOG.debug(self, 'Account close failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account close failed with API error code = %s', error_code)
            return False

        # Success
        return True

    def account_modify(self):
        """Modify an existing account on the server."""
        try:
            jo = self.post_request(APIQuery.ACCOUNT_MODIFY)
        except ClientException:
            LOG.debug(self, 'Account modify failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account modify failed with API error code = %s', error_code)
            return False

        # Success
        return True

    def post_request(self, api_query):
        """Post the request and return the json object (Python dictionary) or raise an exception."""
        url = self.base_url + api_query
        url += APIQuery.KEY + self.key
        url += APIQuery.EMAIL + self.email
        url += APIQuery.PASSWORD + self.password

        LOG.debug(self, 'url = %s', url)

        try:
            response = requests.post(url)
        except Exception as e:
            LOG.debug(self, 'Request post failed with exception = %s', e)
            raise ClientException

        try:
            jo = self.get_json_object(response)
        except ClientException:
            raise ClientException

        # Success.
        return jo

    @staticmethod
    def get_json_object(response):
        """Get the json object (Python dictionary) from the response or raise an exception."""

        LOG.debug(Client, 'status_code = %s', response.status_code)
        LOG.debug(Client, 'content = %s', response.content)

        if response.status_code != HTTP.OK:
            LOG.debug(Client, 'HTTP status code != HTTP.OK')
            raise ClientException

        try:
            jo = JSON.loads(response.content)
        except Exception as e:
            LOG.debug(Client, 'JSON.loads exception = %s', e)
            raise ClientException

        if not type(jo) is dict:
            LOG.debug(Client, 'Type of jo is not an object/dict.')
            raise ClientException

        if not JSONKey.ERROR in jo:
            LOG.debug(Client, 'The decoded jo has no `error` key.')
            raise ClientException

        # Success.
        return jo


class ClientException(Exception):
    """Custom exception class."""

    pass
