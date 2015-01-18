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

from common import APIRequestType, JSONKey, APIErrorCode, HTTP, JSON, Logger, APIURL, \
    AccountModifyRequestBody

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
            self.post_request(APIRequestType.TEST)
        except ClientException:
            LOG.debug(self, 'Check connection failed with an exception.')
            return False

        # Success
        return True

    def check_authentication(self):
        """Check that authentication against an account on the server succeeds."""
        try:
            jo = self.post_request(APIRequestType.TEST)
        except ClientException:
            LOG.debug(self, 'Check authentication failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Check authentication failed with API error code = %s', error_code)
            LOG.debug(self, 'Check authentication failed with API error name = %s',
                      APIErrorCode.name(error_code))
            return False

        # Success
        return True

    def account_open(self):
        """Open a new account on the server."""
        try:
            jo = self.post_request(APIRequestType.ACCOUNT_OPEN)
        except ClientException:
            LOG.debug(self, 'Account open failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account open failed with API error code = %s', error_code)
            LOG.debug(self, 'Account open failed with API error name = %s',
                      APIErrorCode.name(error_code))
            return False

        # Success
        return True

    def account_close(self):
        """Close an existing account on the server."""
        try:
            jo = self.post_request(APIRequestType.ACCOUNT_CLOSE)
        except ClientException:
            LOG.debug(self, 'Account close failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account close failed with API error code = %s', error_code)
            LOG.debug(self, 'Account close failed with API error name = %s',
                      APIErrorCode.name(error_code))
            return False

        # Success
        return True

    def account_modify(self, new_email, new_password):
        """Modify an existing account on the server."""
        request_body = AccountModifyRequestBody()
        request_body.email = new_email
        request_body.password = new_password

        try:
            js = self.get_json_request_string(request_body)
        except ClientException:
            LOG.debug(self, 'Account modify failed with an exception.')
            return False

        try:
            jo = self.post_request(APIRequestType.ACCOUNT_MODIFY, js)
        except ClientException:
            LOG.debug(self, 'Account modify failed with an exception.')
            return False

        error_code = jo[JSONKey.ERROR]

        if error_code != APIErrorCode.SUCCESS:
            LOG.debug(self, 'Account modify failed with API error code = %s', error_code)
            LOG.debug(self, 'Account modify failed with API error name = %s',
                      APIErrorCode.name(error_code))
            return False

        # Success
        return True

    def get_json_request_string(self, model):
        """Get json request string from model or raise a ClientException."""
        # Validate before conversion.
        try:
            model.validate()
        except Exception as e:
            LOG.debug(self, 'Validate exception = %s' % e)
            raise ClientException

        try:
            js = JSON.dumps(model.to_primitive())
        except Exception as e:
            LOG.debug(self, 'JSON dumps exception = %s' % e)
            raise ClientException

        return js

    def post_request(self, api_request_type, data=None):
        """Post the request and return the json object (Python dictionary) or raise an exception."""

        url_string = self.get_url_string(api_request_type)

        LOG.debug(self, 'url = %s', url_string)

        headers = {'Accept': 'application/json',
                   'User-Agent': 'TuckerSync'}

        if data:
            headers['Content-Type'] = 'application/json'

        try:
            response = requests.post(url_string, data, headers=headers)
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

    def get_url_string(self, api_request_type):
        """Construct a url string from this clients settings."""
        url = APIURL()
        url.base_url = self.base_url
        url.type = api_request_type
        url.key = self.key
        url.email = self.email
        url.password = self.password
        return url.url_string()


class ClientException(Exception):
    """Custom exception class."""

    pass
