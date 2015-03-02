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
from schematics.types import StringType, LongType, BooleanType


class BaseAppModel(Model):
    """Base app model class. Application model classes must inherit from this class."""

    rowid = LongType()
    originClientId = LongType()
    originClientObjectId = LongType()
    lastUpdatedByClientId = LongType()
    ownerUserId = LongType()
    lastSync = LongType()
    deleted = BooleanType(default=0)


class Setting(BaseAppModel):
    """Setting is an example application database model."""

    name = StringType()
    value = StringType()

    SELECT_BY_ID = """SELECT id as rowid,
            originClientId,
            originClientObjectId,
            lastUpdatedByClientId,
            ownerUserId,
            lastSync,
            deleted,
            name,
            value
        FROM Setting WHERE id = %s"""

    def select_by_id_params(self):
        return self.rowid,

    INSERT = """INSERT INTO Setting (
            originClientId,
            originClientObjectId,
            lastUpdatedByClientId,
            ownerUserId,
            lastSync,
            deleted,
            name,
            value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    def insert_params(self):
        return (self.originClientId,
                self.originClientObjectId,
                self.lastUpdatedByClientId,
                self.ownerUserId,
                self.lastSync,
                self.deleted,
                self.name,
                self.value)


class Product(BaseAppModel):
    """Product is an example application database model."""

    name = StringType()

    SELECT_BY_ID = """SELECT id as rowid,
            originClientId,
            originClientObjectId,
            lastUpdatedByClientId,
            ownerUserId,
            lastSync,
            deleted,
            name
        FROM Setting WHERE id = %s"""

    def select_by_id_params(self):
        return self.rowid,

    INSERT = """INSERT INTO Product (
            originClientId,
            originClientObjectId,
            lastUpdatedByClientId,
            ownerUserId,
            lastSync,
            deleted,
            name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    def insert_params(self):
        return (self.originClientId,
                self.originClientObjectId,
                self.lastUpdatedByClientId,
                self.ownerUserId,
                self.lastSync,
                self.deleted,
                self.name)
