Tucker Sync API
===============

Synchronisation over HTTPS, using POST and JSON.
*Version 0.4*

Motivation
----------

With the advent of multiple device per user mobile computing, synchronising data has become a very common operation. Put simply synchronisation is an expected feature of any application that works with data. While there still appears to be a dearth of complete, clearly explained patterns or sync algorithms in the open source world. This API hopes to provide a better starting point. Two way, three way and more way sync ;-)

Complete with client and server implementation (Python and PHP).

[Tucker Sync API is very much a work in progress, we hope to have a version 1.0 release in due course.]

Terminology
-----------

A **client** is identified uniquely in the server-client relationship.  
A **user** is identified uniquely and may have multiple clients running on different devices.  
A **device** may have multiple users and each is a unique client.  

syncCount - camel case indicates a server value.  
last_sync - underscore indicates a client value.  

Operation
---------

Synchronisation is always initiated by the client application.  
Although it may be prompted to do so by another channel, for example a Cloud Messaging Service.

Sync occurs in two phases:

**Download Phase** - client requests new and remotely changed objects from server since last sync.  
**Upload Phase** - client uploads new and locally changed objects to the server.  

The server maintains a universal sync counter (syncCount).  
This is used in preference to the more fickle timestamp sometimes used in sync API.  

Download Phase
--------------

For each object class:

 - The **client** requests new and changed objects since last_sync:
     - SELECT last_sync FROM object_class ORDER BY last_sync DESC LIMIT 1;
 - The **server** returns objects, for object_class and user where (lastSync > last_sync).
 - For each object returned the **client**:
     - Inserts or updates the object based on server_object_id.
     - Using all of the server provided values and setting local_changes=0.
     - Hence server always wins a.k.a. first-in-first-served or discard type conflict resolution.

Upload Phase
------------

For each object class:

 - The **client** may create objects locally and must set:
     -  server_object_id=0, last_sync=0 and local_changes=1.
 - The **client** may update objects locally and must set:
     -  local_changes=1.
 - The **client** uploads objects to the server (where local_changes=1).
 - The **server** performs an insert on new objects (where server_object_id=0).
 - The **server** performs an update on existing objects:
     - by server_object_id and lastSync < last_sync and client_id is authorised.
     - conflicts are resolved by lastSync, highest winning, since it’s a newer version.
 - The **server** returns an error code and all of the objects.
 - The **client** updates local objects by clientObjectId:
     - with the supplied serverObjectId and lastSync
     - setting local_changes=0

This pattern would generally sync all objects in a class. With an arbitrary maximum data payload of say 5MB. But sync payloads could be chunked by either side if required.

UUIDs are not used to identify objects due to their size impact on the client. Instead the client generates a single UUID to identify itself to the server and sends it’s local id for each object thus allowing the server to identify duplicate new objects. Achieved by setting a unique constraint, see Server Schema.

All requests require an application key to be provided in the query. This is a private key only known to the server and client. If not required the key may be set to an empty string ("") in both the server and client configurations.

An unauthenticated base data download may be performed to pull any base data objects. All other requests require authentication by email and password against an account on the server. The account open request uses the email and password to create and then authenticate an account.

The client should probably perform a background sync on startup and a blocking/modal sync during operation with background on exit. The client may wish to perform a base data download on first start.

**Base URL Example**  
https://api.app.example.com/  
(Use a .htaccess rewrite rule with index.php)  

Test Request
------------

**Summary** - Test the connection and server availability.

**Function** - The test function will perform some basic availability tests on the server and reply with the appropriate error value. The client should inspect the API error code to determine that the server is available and functioning correctly. This call can be useful when first contacting the server, or after a failed communication to check the server before trying again. The matching API error code will be returned to indicate whether authentication succeeded or not and thus both connection and authentication can be checked separately.

**Request**  
Query: ?type=test  
Method: POST  

*Example request URL:*

    https://api.app.example.com/?type=test&key=private&email=user@example.com&password=secret

*Example request body:*

    None

**Response**  
Message Body: JSON object containing error code.

*Example response code:* 200  
*Example response body:*  

    {"error":1}

Base Data Download Request
--------------------------

**Summary** - Download base data objects for class.

**Function** - A server may provide a set of base data for an object class. This request does not require authentication (email and password). But does require the application key.

**Request**  
Query: ?type=baseDataDown  
Method: POST  
Message Body: JSON object containing objectClass, lastSync and clientUUID.

*Example request URL:*

    https://api.app.example.com/?type=baseDataDown&key=private

*Example request body:*

    {"objectClass":"product","clientUUID":"UUID","lastSync":123}

**Response**  
Message Body: JSON object containing error and objects.

*Example response code:* 200  
*Example response body:*

    {"error":0,"objects":[{"serverObjectId":1,"lastSync":124},{"serverObjectId":n}]}

Sync Download Request
---------------------

**Summary** - Synchronise objects for class.

**Function** - Sync logical data objects between client and server for backup, replication and sharing purposes.

**Request**  
Query: ?type=syncDown  
Method: POST  
Message Body: JSON object containing objectClass, lastSync and clientUUID.  

*Example request URL:*

    https://api.app.example.com/?type=syncDown&key=private&email=user@example.com&password=secret

*Example request body:*

    {"objectClass":"product","clientUUID":"UUID","lastSync":123}

**Response**  
Message Body: JSON object containing error and objects.

*Example response code:* 200  
*Example response body:*

    {"error":0,"objects":[{"serverObjectId":1,"lastSync":124},{"serverObjectId":n}]}

Sync Upload Request
-------------------

**Summary** - Synchronise objects for an object class.

**Function** - Sync logical data objects between client and server for backup, replication and sharing purposes.

**Request**  
Query: ?type=syncUp  
Method: POST  
Message Body: JSON object containing objectClass, clientUUID and objects.

*Example request URL:*

    https://api.app.example.com/?type=syncUp&key=private&email=user@example.com&password=secret

*Example request body:*

    {"objectClass":"product","clientUUID":"UUID","objects":[{"serverObjectId":0},{"serverObjectId":n}]}

**Response**  
Message Body: JSON object containing error and objects.

*Example response code:* 200  
*Example response body:*  

    {"error":0,"objects":[{"serverObjectId":1,"lastSync":125},{"serverObjectId":n}]}

Account Requests
----------------

**Summary** - Allow user to manage their account on the server.

**Function** - The account open request will use the query email and password to create an account on the server, additional account data may be placed in the request body. The account close and modify requests will use the query email and password for authentication. The account modify must supply the changed values in the request body.

**Request**  
Query: ?type=accountOpen | accountClose | accountModify  
Method: POST  
Message Body: JSON object containing data  

*Example request URL:*

    https://api.app.example.com/?type=accountOpen&key=private&email=user@example.com&password=secret

*Example request body:*

accountModify:

    {"email":"new_user@example.com","password":"new_password"}

**Response**  
Message Body: JSON object containing error and data.

*Example response code:* 200  
*Example response body:*  

    {"error":0}

Errors
------

PHP:

    class Errors
    {
        const SUCCESS = 0;
        const INTERNAL_SERVER_ERROR = 1;
        const MALFORMED_REQUEST = 2;
        const INVALID_KEY = 3;
        const INVALID_EMAIL = 4;
        const INVALID_PASSWORD = 5;
        const AUTH_FAIL = 6;
        const INVALID_JSON_OBJECT = 7;
        const EMAIL_NOT_UNIQUE = 8;
        const CLIENT_UUID_NOT_UNIQUE = 9;
        const FULL_SYNC_REQUIRED = 10;
    }

Use Cases
---------

New local data object created on client A and backup sync to server.  
Existing local object changed on device A and updated on server.  
Replication to client B.  
Changed object on client B and replicated to client A.  
(user must sync B before A changes the same object).  
Deleted object on client B and replicated to client A.  

New object created by user X on client A and shared with user Y on client C.  

Client Schema
-------------

Required on each object class to be synced:

last_sync - long value, 0 if not synced yet, determined by server and then recorded locally by client.  
local_changes - boolean value, set by client when there are local changed yet to be synced.  
server_object_id - long value, 0 if not synced yet, replaced with server’s id for this object once synced.  

deleted - boolean value, logical deletion on each object to propagate that deletion to other clients.  
Client may perform a cleanup run of physical deletion after sync where deleted=1 and local_changes=0.  

An immediate client physical deletion should not be performed if server_object_id=0.  
Since the server may actually have received a copy during a failed sync where the client did not receive the response.  

Server Schema
-------------

syncCount - universal long (64bit) sync counter, incremented on each successful db transaction.

Required on each object class to be synced:

id - server object id.  
userId - required on each object?  
clientId - the unique client id that created the object.  
clientObjectId - the object id from the client that created the object.  
last_sync - long value, 0 if not synced yet, determined by server and then recorded locally by client.  

The clientId and clientObjectId together form a unique constraint. Allowing the server to identify duplicates that the client may resend after a response transmission fails to reach the client:

    unique index `uniqueObjectConstraint` (`clientId`,`clientObjectId`)

**Client**  
id - identifier.  
userId - which user does this client belong to.  
UUID - client supplied UUID.  

**User**  
id - identifier.  
email - acts as username.  
password - standard salted and encrypted.  
accountLevel - server side account levels: free, social (friends & family), professional/coach/trainer/elite/platinum.  
isActive - open=true, closed=false.  

Server Functions
----------------

User Authentication. Account management. Account upgrade.

[Not implemented in this version]  
Manage data permissions and roles (ACL).

Further server functions may be defined in the application spec template.

Server Protections
------------------

The server should perform sanity checks on every incoming request:

 - last_sync > syncCount - if true, return the FULL_SYNC_REQUIRED error. The client must set local_changes=1 on all objects and resend all objects. (This might happen if the server fails or a new server is setup or client gets out of sync)

To restore a failed server from backup:

 - The server must set it’s syncCount to the highest lastSync value found by examining all object classes.

[Not implemented in this version]  
Include API version, clientAppName, clientAppVersion in each call. Allows at least refusing to serve very old clients or reverting to a previous API compatibility mode.

Logical Objects
---------------

To use this API logical data objects must be defined for your application.  
These may be defined in the application spec template.  

For example you may have a logging application, where a logEntry has a date value and a list of measurements.

Requiring two data objects:

    LogEntry {
        String date
        List<Measurement> measurementList
    }

    Measurement {
        int value
    }

Rewrite Rule
------------

For clean URL’s place these rewrite rules in the server document root.

.htaccess:

    # BEGIN Sync API

    <IfModule mod_rewrite.c>
       RewriteEngine On
       RewriteBase /
       RewriteRule ^index\.php$ - [L]
       RewriteCond %{REQUEST_FILENAME} !-f
       RewriteCond %{REQUEST_FILENAME} !-d
       RewriteRule . /index.php [L]
    </IfModule>

    # END Sync API

OR

    # BEGIN Sync API
    <IfModule mod_rewrite.c>
       RewriteEngine On
       RewriteCond %{REQUEST_FILENAME} !-f
       RewriteRule ^(.*)$ index.php?_url=/$1 [QSA,L]
    </IfModule>
    # END Sync API

Extra
-----

This document is written in the markdown (.md) format.  
Using the dialects as supported by GitHub, Intellij IDEA and stackedit.io.  

HTTP(S)/1.1 is used and data errors are kept separate from communication errors.

JSON (ECMA-404) is the data interchange format.  
JSON API (http://jsonapi.org/) looks fairly sensible although probably not thoroughly conformed to.  
JSON Schema (http://json-schema.org/) may also be of some interest although not currently used.  

Python 2.6 used for development (should then run on 2.6 - 3.3).  
Web.py (http://webpy.org/) is currently used for the Python server implementation.  
Requests is used for the Python client implementation.  
Pytest is used for test suite.  
Sqlite3 and MySQL are the databases used in the implementation examples.  

The target PHP version will be 5.4 (should then run on >= 5.4).  

Git of course is the SCM.  

Project IDE files are IntelliJ IDEA (the free PyCharm or IDEA Ultimate with Python plugin).  
Run configurations for server, client and tests are included.

License
-------

The MIT License (MIT)

Copyright (c) 2014 Steven Tucker and Gavin Kromhout

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

