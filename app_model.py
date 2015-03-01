"""Application defined database model classes.

Models must define the items required for the server to handle your application logical data
objects. Follow the examples provided closely.

Application models are created using Schematics:
    Python Data Structures for Humans(TM)
    https://github.com/schematics/schematics
    http://schematics.readthedocs.org

Usage:
    Create model classes to define the logical data objects for your application.
    Create a matching MySQL database, user, permissions and tables.
    (See app_create.sql and app_drop.sql)
    Set the database connection properties.
    (See app_config.sql)

    Models must be in app_model.py for automatic inclusion. But of course you can create your own
    application app_model.py file with your own license.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

from schematics.models import Model
from schematics.types import StringType, LongType


class Setting(Model):
    """Setting is an example application database model."""

    rowid = LongType()
    clientId = LongType()
    clientObjectId = LongType()
    lastSync = LongType()
    name = StringType()
    value = StringType()

    SELECT_BY_ID = """SELECT id as rowid, clientId, clientObjectId, lastSync, name, value
        FROM Setting WHERE id = %s"""

    def select_by_id_params(self):
        return self.rowid,

    INSERT = """INSERT INTO Setting (clientId, clientObjectId, lastSync, name, value)
                  VALUES (%s, %s, %s, %s, %s)"""

    def insert_params(self):
        return self.clientId, self.clientObjectId, self.lastSync, self.name, self.value


class Product(Model):
    """Product is an example application database model."""

    rowid = LongType()
    clientId = LongType()
    clientObjectId = LongType()
    lastSync = LongType()
    name = StringType()

    SELECT_BY_ID = """SELECT id as rowid, clientId, clientObjectId, lastSync, name
        FROM Product WHERE id = %s"""

    def select_by_id_params(self):
        return self.rowid,

    INSERT = """INSERT INTO Product (clientId, clientObjectId, lastSync, name)
                  VALUES (%s, %s, %s, %s)"""

    def insert_params(self):
        return self.clientId, self.clientObjectId, self.lastSync, self.name
