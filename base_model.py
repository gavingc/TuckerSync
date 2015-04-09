"""Base application database model class.

Provides the base for application models.
Defines the base required fields.
Defines the base required functions of application object classes to be synced.

Usage:
    See app_model.py

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

from six import iterkeys

from schematics.models import Model
from schematics.types import LongType, BooleanType

SELECT = 'SELECT'
INSERT = 'INSERT'
INTO = 'INTO'
VALUES = 'VALUES'
FROM = 'FROM'
WHERE = 'WHERE'
SEP = ',\n  '


class BaseAppModel(Model):
    """Base application model class.

    Application model classes must inherit from this class."""

    # Required fields.
    # Do not override in subclasses.
    rowid = LongType()
    originClientId = LongType()
    originClientObjectId = LongType()
    lastUpdatedByClientId = LongType()
    ownerUserId = LongType()
    lastSync = LongType()
    deleted = BooleanType(default=0)

    def columns(self):
        columns = self.keys()
        columns.remove('rowid')
        columns.insert(0, 'id')
        return columns

    def select_by_id(self):
        return '\n'.join([SELECT,
                          '  ' + SEP.join(self.columns()),
                          FROM,
                          '  ' + self.__class__.__name__,
                          WHERE,
                          '  ' + 'id = %s'])

    def select_by_id_params(self):
        return self.rowid,

    def insert(self):
        table = self.__class__.__name__
        columns = self.keys()
        columns.remove('rowid')
        values = ('%s' for _ in xrange(len(columns)))

        return '\n'.join([INSERT + ' ' + INTO + ' ' + table + ' (',
                          '  ' + SEP.join(columns),
                          ')',
                          VALUES + ' ( ',
                          '  ' + ', '.join(values),
                          ')'])

    def insert_params(self):
        return tuple(
            self.get(k) for k in iterkeys(self._fields) if k is not 'rowid')
