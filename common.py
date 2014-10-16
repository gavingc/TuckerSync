#!env/bin/python
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Steven Tucker and Gavin Kromhout
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import json


class APIQuery(object):
    """The API query constants."""

    TEST = "?type=test"
    SYNC_DOWN = "?type=syncDown"
    SYNC_UP = "?type=syncUp"


class JSONKey(object):
    """The JSON key constants."""

    ERROR = "error"
    DATA = "data"
    OBJECTS = "objects"


class APIErrorCode(object):
    """The API error code constants."""

    SUCCESS = 0
    UNKNOWN = 1
    FULL_SYNC_REQUIRED = 10


class HTTP(object):
    """HTTP constants."""

    OK = 200


class JSON(object):
    """Custom json wrapper."""

    COMPACT_SEPARATORS = (',', ':')

    @staticmethod
    def dumps(obj):
        """Dump an object to a compact json string."""
        return json.dumps(obj, separators=JSON.COMPACT_SEPARATORS)

    @staticmethod
    def loads(s):
        """Load a string and return a Python native json object."""
        return json.loads(s)

    @staticmethod
    def load(fp):
        """Load (read) a file like object and return a Python native json object."""
        return json.load(fp)
