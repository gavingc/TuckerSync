"""Application defined database model classes.

Models must define the items required for the server to handle your application
logical data objects. Follow the examples provided closely.

Application models are created using Schematics:
    Python Data Structures for Humans(TM)
    https://github.com/schematics/schematics
    http://schematics.readthedocs.org

Usage:
    Create model classes to define data objects for your application.
    Create a matching MySQL database, user, permissions and tables.
    (See app_create.sql and app_drop.sql)
    Set the database connection properties.
    (See app_config.sql)

    Models must be in app_model.py for automatic inclusion.
    But of course you can create your own application app_model.py file with
    your own license.

    Import from schematics.types, available types including:
        StringType, LongType, BooleanType, URLType, EmailType, DateType...

Beware:
    Not to accidentally override the required fields defined in BaseAppModel.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

from schematics.types import StringType

from base_model import BaseAppModel


class Setting(BaseAppModel):
    """Setting is an example application database model."""

    name = StringType()
    value = StringType()


class Product(BaseAppModel):
    """Product is an example application database model."""

    name = StringType()
