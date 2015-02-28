#!env/bin/python

"""Test suite for the Tucker Sync algorithm, sync count.

The goal of this test module is to explore, document and prove the sync count and database state.
By exercising the actual SQL statements, sequences and functions.

This module is not intended to be run often or test the server function.

New database connections are used for clean results between functions.
In some cases `cursor.execute('COMMIT')` is purposely used instead of `cnx.commit()`.
Since the 'COMMIT' statement is used in common.py statements.
Also in the version of Connector/Python explored cnx.commit() simply executes 'COMMIT'.

Where sessions a and b are run in new processes.
This allows genuine parallel execution of the session code in Python.

Usage:
    ./test_sync_count.py --help
    or
    See main().

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

from time import sleep, time
from uuid import uuid4

from tests import main
from server import execute_statement, execute_statements, open_db, _close_db
from common import SyncCount


class Product(object):
    """Object class model stub."""
    pass


class Setting(object):
    """Object class model stub."""
    pass


def drop_create_tables():
    """Drop and create database tables helper function."""

    # Config opens connection with raise_on_warnings=True
    cursor, cnx, errno = open_db()
    assert None == errno

    files = ('drop-app.sql', 'drop-base.sql', 'create-base.sql', 'create-app.sql')

    # MySQL generates warnings for DROP IF EXISTS statements against nonexistent tables.
    # These warnings are 'Note level'.
    # http://dev.mysql.com/doc/refman/5.6/en/drop-table.html
    # http://bugs.mysql.com/bug.php?id=2839
    # http://dev.mysql.com/doc/refman/5.0/en/server-system-variables.html#sysvar_sql_notes

    # Connector/Python has an issue/bug fetching warnings when multi=True and then actually
    # executing multiple statements with any warnings.
    # An InterfaceError is raised and execution cannot continue.

    # To prevent this get_warnings may be disabled for multi=True, or `SET sql_notes = 0`.
    # Setting/Clearing raise_on_warnings also sets/clears get_warnings.
    # cnx.raise_on_warnings = False
    # OR
    stmt = """SET sql_notes = 0"""
    cursor.execute(stmt)

    for fl in files:
        with open(fl) as f:
            statements = f.read()

        for result in cursor.execute(statements, multi=True):
            # Errors will raise but no warning checking is available.
            # MySQL warnings greater than note level may raise a misleading error.
            assert -1 != result.rowcount

    _close_db(cursor, cnx)


def new_client_id():
    """New client id helper function. Inserts a user and client, returns the client id."""

    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO User (email, password) VALUES (%s, %s)"""

    email = str(uuid4()) + '@example.com'
    password = '$5$rounds=115483$3nGzDt/Fs31t064H$GgwVigNlOTBXoh2YXy0UsQEdzx.deJqLha3vpLomKm6'
    # password: secret78901234
    params = (email, password)

    cursor.execute(statement, params)
    assert 1 == cursor.rowcount

    statement = """INSERT INTO Client (userId, UUID) VALUES (LAST_INSERT_ID(), %s)"""
    params = (str(uuid4()),)

    cursor.execute(statement, params)
    assert 1 == cursor.rowcount
    cnx.commit()

    return cursor.lastrowid


def get_committed_sc_x(object_class):
    """Get committed sync count for object class by executing the statement.

    Allows SELECT_COMMITTED_SC statement to be tested under various sync states."""

    cursor, cnx, errno = open_db()
    assert None == errno

    committed_sc = SyncCount()
    committed_sc.object_class = object_class.__name__

    cursor.execute(SyncCount.SELECT_COMMITTED_SC,
                   committed_sc.select_committed_sc_params())

    rows = cursor.fetchall()
    assert 1 == len(rows)
    assert 1 == cursor.rowcount
    assert None == cursor.lastrowid

    committed_sc.sync_count = rows[0]['sync_count']

    _close_db(cursor, cnx)

    return committed_sc


def get_session_sc_x(object_class, insert_commit=True):
    """Get session sync count for object class by executing the sequence of statements."""

    cursor, cnx, errno = open_db()
    assert None == errno

    session_sc = SyncCount()
    session_sc.object_class = object_class.__name__

    cursor.execute(SyncCount.INSERT, session_sc.insert_params())

    assert 1 == cursor.rowcount
    insert_rowid = cursor.lastrowid
    assert 0 < insert_rowid

    if insert_commit:
        cursor.execute('COMMIT')

    cursor.execute(SyncCount.DELETE_TRAILING_COMMITTED,
                   session_sc.delete_trailing_committed_params())

    assert -1 != cursor.rowcount
    assert 0 == cursor.lastrowid

    cursor.execute('COMMIT')

    cursor.execute('SELECT LAST_INSERT_ID() AS sync_count')

    rows = cursor.fetchall()
    assert 1 == len(rows)
    assert 1 == cursor.rowcount
    assert 0 == cursor.lastrowid

    session_sc.sync_count = rows[0]['sync_count']

    _close_db(cursor, cnx)

    assert insert_rowid == session_sc.sync_count

    return session_sc


def mark_session_committed_x(session_sync_count):
    """Mark session as committed by executing the statements."""

    cursor, cnx, errno = open_db()
    assert None == errno

    # Data transaction statements would be here.

    cursor.execute(SyncCount.UPDATE_SET_IS_COMMITTED,
                   session_sync_count.update_set_is_committed_params())

    assert 1 == cursor.rowcount
    assert 0 == cursor.lastrowid

    # Commit both the data and mark the session as committed.
    cnx.commit()

    # Catch any data transaction exception then execute and commit UPDATE_SET_IS_COMMITTED again.

    _close_db(cursor, cnx)


def mark_expired_sessions_committed_x(object_class):
    """Mark expired sessions as committed by executing the statements. Return rowcount."""

    cursor, cnx, errno = open_db()
    assert None == errno

    sc = SyncCount()
    sc.object_class = object_class.__name__

    cursor.execute(SyncCount.UPDATE_SET_IS_COMMITTED_EXPIRED,
                   sc.update_set_is_committed_expired_params())

    rowcount = cursor.rowcount
    assert 0 == cursor.lastrowid
    cnx.commit()

    _close_db(cursor, cnx)

    return rowcount


def session_sequence_x(object_class):
    """Execute the session sequence for a single object class."""

    # Sequence Start #
    mark_expired_sessions_committed_x(object_class)

    # Session sync count for use in data transaction.
    session_sc = get_session_sc_x(object_class)

    # Perform data transaction and mark session committed.
    mark_session_committed_x(session_sc)

    # Committed sync count for return to client.
    committed_sc = get_committed_sc_x(Product)

    # Sequence End #
    return session_sc, committed_sc


###################################
## Test Get Committed Sync Count ##
###################################


def test_get_committed_sc_no_rows():
    """Test getting the committed sync count with no rows and fresh tables."""

    drop_create_tables()

    committed_sc = get_committed_sc_x(Product)
    assert 0 == committed_sc.sync_count


def test_get_committed_sc_0():
    """Test getting the committed sync count with a single uncommitted session."""

    drop_create_tables()

    # Insert Single Row with Session Marked Uncommitted #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES (%s, %s)"""
    params = (Product.__name__, 0)

    cursor.execute(statement, params)
    assert 1 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 0 == committed_sc.sync_count


def test_get_committed_sc_1():
    """Test getting the committed sync count with a single committed session."""

    drop_create_tables()

    # Insert Single Row with Session Marked Committed #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES (%s, %s)"""
    params = (Product.__name__, 1)

    cursor.execute(statement, params)
    assert 1 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 1 == committed_sc.sync_count


def test_get_committed_sc_0_1():
    """Test getting the committed sync count with an uncommitted and following committed session."""

    drop_create_tables()

    # Insert Uncommitted and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES (%s, %s), (%s, %s)"""
    params = (Product.__name__, 0, Product.__name__, 1)

    cursor.execute(statement, params)
    assert 2 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 0 == committed_sc.sync_count


def test_get_committed_sc_1_0():
    """Test getting the committed sync count with a committed and following uncommitted session."""

    drop_create_tables()

    # Insert Committed and Following Uncommitted Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES (%s, %s), (%s, %s)"""
    params = (Product.__name__, 1, Product.__name__, 0)

    cursor.execute(statement, params)
    assert 2 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 1 == committed_sc.sync_count


def test_get_committed_sc_1_1():
    """Test getting the committed sync count with a committed and following committed session."""

    drop_create_tables()

    # Insert Committed and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES (%s, %s), (%s, %s)"""
    params = (Product.__name__, 1, Product.__name__, 1)

    cursor.execute(statement, params)
    assert 2 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 2 == committed_sc.sync_count


def test_get_committed_sc_1101100():
    """Test getting the committed sync count with complex committed and uncommitted sessions."""

    drop_create_tables()

    # Insert Committed and UnCommitted Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Product.__name__, 1),
                     (Product.__name__, 1),
                     (Product.__name__, 0),
                     (Product.__name__, 1),
                     (Product.__name__, 1),
                     (Product.__name__, 0),
                     (Product.__name__, 0))

    cursor.executemany(statement, seq_of_params)
    assert 7 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 2 == committed_sc.sync_count


def test_get_committed_sc_0010011():
    """Test getting the committed sync count with complex committed and uncommitted sessions."""

    drop_create_tables()

    # Insert Committed and UnCommitted Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Product.__name__, 0),
                     (Product.__name__, 0),
                     (Product.__name__, 1),
                     (Product.__name__, 0),
                     (Product.__name__, 0),
                     (Product.__name__, 1),
                     (Product.__name__, 1))

    cursor.executemany(statement, seq_of_params)
    assert 7 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Product)
    assert 0 == committed_sc.sync_count


def test_get_committed_sc_mixed_object_class_1100():
    """Test getting the committed sync count with mixed object classes."""

    drop_create_tables()

    # Insert Committed and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Setting.__name__, 1),
                     (Product.__name__, 1),
                     (Product.__name__, 0),
                     (Setting.__name__, 0))

    cursor.executemany(statement, seq_of_params)
    assert 4 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Setting)
    assert 3 == committed_sc.sync_count
    committed_sc = get_committed_sc_x(Product)
    assert 2 == committed_sc.sync_count


def test_get_committed_sc_mixed_object_class_0011():
    """Test getting the committed sync count with mixed object classes."""

    drop_create_tables()

    # Insert Committed and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Setting.__name__, 0),
                     (Product.__name__, 0),
                     (Product.__name__, 1),
                     (Setting.__name__, 1))

    cursor.executemany(statement, seq_of_params)
    assert 4 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Setting)
    assert 0 == committed_sc.sync_count
    committed_sc = get_committed_sc_x(Product)
    assert 1 == committed_sc.sync_count


def test_get_committed_sc_mixed_object_class_1010():
    """Test getting the committed sync count with mixed object classes."""

    drop_create_tables()

    # Insert Committed and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Setting.__name__, 1),
                     (Product.__name__, 0),
                     (Product.__name__, 1),
                     (Setting.__name__, 0))

    cursor.executemany(statement, seq_of_params)
    assert 4 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Setting)
    assert 3 == committed_sc.sync_count
    committed_sc = get_committed_sc_x(Product)
    assert 1 == committed_sc.sync_count


def test_get_committed_sc_mixed_object_class_1110():
    """Test getting the committed sync count with mixed object classes."""

    drop_create_tables()

    # Insert Committed and Following Committed Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    seq_of_params = ((Setting.__name__, 1),
                     (Product.__name__, 1),
                     (Product.__name__, 1),
                     (Setting.__name__, 0))

    cursor.executemany(statement, seq_of_params)
    assert 4 == cursor.rowcount
    cnx.commit()

    _close_db(cursor, cnx)

    # Assert Result #
    committed_sc = get_committed_sc_x(Setting)
    assert 3 == committed_sc.sync_count
    committed_sc = get_committed_sc_x(Product)
    assert 3 == committed_sc.sync_count


#################################
## Test Get Session Sync Count ##
#################################


def test_get_session_sc_parallel_long_trailing_delete_insert_commit_false():
    """Results suggests that insert_commit is required.

    Although a little contrived since two object classes are used leaving session b free to
    return quickly as it's delete is not affecting the same rows as session a's delete."""

    obj_classes = [Product, Setting]

    a_finish, b_finish, a_session_sc, b_sc_list = \
        t_get_session_sc_parallel_long_trailing_delete(obj_classes, insert_commit=False)

    print 'a_finish =', a_finish
    print 'b_finish =', b_finish
    print 'b_finish - a_finish (s) =', b_finish - a_finish

    print 'a_session_sc =', a_session_sc.sync_count
    print 'b_sc_list =', b_sc_list

    # b finishes first, always.
    assert b_finish < a_finish

    assert 100001 == a_session_sc.sync_count
    assert [99999, 100000, 100002] == b_sc_list

    # For the algorithm to operate correctly, a_session_sc should be in the list.
    # But it is not.
    assert a_session_sc.sync_count not in b_sc_list


def test_get_session_sc_parallel_long_trailing_delete_insert_commit_false2():
    """Results show that without insert_commit session b's delete must wait for a's delete.

    Since the same object classes are used for both sessions.
    Also shows that b's trailing delete is very fast on the normal handful or rows."""

    obj_classes = [Product, Product]

    a_finish, b_finish, a_session_sc, b_sc_list = \
        t_get_session_sc_parallel_long_trailing_delete(obj_classes, insert_commit=False)

    print 'a_finish =', a_finish
    print 'b_finish =', b_finish
    print 'b_finish - a_finish (s) =', b_finish - a_finish

    print 'a_session_sc =', a_session_sc.sync_count
    print 'b_sc_list =', b_sc_list

    # a finishes first (only just), showing that b was held up.
    # Connector InternalError: Deadlock - seen once.
    assert b_finish > a_finish

    assert 100001 == a_session_sc.sync_count
    assert [100001, 100002] == b_sc_list

    # For the algorithm to operate correctly, a_session_sc must be in the list.
    # a_session_sc is in the list but only because b's delete was serialised.
    assert a_session_sc.sync_count in b_sc_list


def test_get_session_sc_parallel_long_trailing_delete_insert_commit_true():
    """Results show that with insert_commit session b's delete may not have to wait for a's delete.

    The same object classes are used for both sessions.
    Also shows that b's trailing delete is very fast on the normal handful or rows."""

    obj_classes = [Product, Product]

    a_finish, b_finish, a_session_sc, b_sc_list = \
        t_get_session_sc_parallel_long_trailing_delete(obj_classes, insert_commit=True)

    print 'a_finish =', a_finish
    print 'b_finish =', b_finish
    print 'b_finish - a_finish (s) =', b_finish - a_finish

    print 'a_session_sc =', a_session_sc.sync_count
    print 'b_sc_list =', b_sc_list

    # b finishes first, most of the time.
    assert b_finish < a_finish

    # Note that 100002 would be b's session sync count.
    assert 100001 == a_session_sc.sync_count
    assert [100001, 100002] == b_sc_list

    # For the algorithm to operate correctly, a_session_sc must be in the list.
    assert a_session_sc.sync_count in b_sc_list


def t_get_session_sc_parallel_long_trailing_delete(obj_classes, insert_commit=True):
    """Parallel Sessions with long running trailing delete.

    Session a and b are run in new processes.
    Session a's session sync count must be visible to session b to cause b's committed sync count
    to be lower than it.

    Note that b's trailing delete may return quickly if it does not affect the same rows as
    session a."""

    from multiprocessing import Process, Queue

    drop_create_tables()

    # Pre-load Rows to Create a Long Trailing Delete #
    cursor, cnx, errno = open_db()
    assert None == errno
    statement = """INSERT INTO SyncCount (objectClass, isCommitted) VALUES (%s, %s)"""
    params = (obj_classes[0].__name__, 1)
    seq_params = []
    for i in xrange(10000):
        seq_params.append(params)

    start_time = time()
    for i in xrange(10):
        cursor.executemany(statement, seq_params)
        cnx.commit()
    duration = time() - start_time
    print 'pre-load duration (s) =', duration
    _close_db(cursor, cnx)
    # Duration is used as an indication of row manipulation execution speed.
    # There must be enough rows to cause a long running trailing delete.
    # If this assert fails then increase the number of pre-load rows and associated test values.
    assert 5 < duration
    # If this assert fails then decrease the number of pre-load rows and associated test values.
    assert 12 > duration

    def run_session_a(q):
        q.put('A Started')
        sess_sc = get_session_sc_x(obj_classes[0], insert_commit=insert_commit)
        finish = time()
        q.put(finish)
        q.put(sess_sc)

    def run_session_b(q):
        q.put('B Started')
        get_session_sc_x(obj_classes[1], insert_commit=insert_commit)
        # Get sync count list
        cur, conn, err = open_db()
        assert None == err
        stmt = """SELECT syncCount FROM SyncCount WHERE syncCount > 99998"""
        cur.execute(stmt)
        rws = cur.fetchall()
        _close_db(cur, conn)
        finish = time()
        q.put(finish)
        q.put(rws)

    a_queue = Queue()
    Process(target=run_session_a, args=(a_queue,)).start()
    assert 'A Started' == a_queue.get()  # blocking call

    # Blocking call above ensures session_a is running before starting session_b.

    b_queue = Queue()
    Process(target=run_session_b, args=(b_queue,)).start()
    assert 'B Started' == b_queue.get()  # blocking call

    a_finish = a_queue.get()
    b_finish = b_queue.get()
    a_session_sc = a_queue.get()
    b_rows = b_queue.get()

    b_sc_list = []
    for r in b_rows:
        b_sc_list.append(r['syncCount'])

    return a_finish, b_finish, a_session_sc, b_sc_list


#################################
## Test Mark Session Committed ##
#################################


def test_mark_session_committed():
    """Test marking session committed."""

    drop_create_tables()

    # Insert a Range of Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    # Insert sessions:
    statements = """INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES ('Product', 0);

                   INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES ('Product', 0);

                   INSERT INTO SyncCount (objectClass, isCommitted)
                   VALUES ('Product', 0);"""

    for result in cursor.execute(statements, multi=True):
        assert 1 == result.rowcount
        # Errors and warnings will raise.

    cnx.commit()
    _close_db(cursor, cnx)

    # Mark session as committed.
    session_sc = SyncCount()
    session_sc.object_class = Product.__name__
    session_sc.sync_count = 2
    mark_session_committed_x(session_sc)

    # Insert a Range of Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno
    statement = """SELECT syncCount, isCommitted FROM SyncCount ORDER BY syncCount"""
    cursor.execute(statement)
    rows = cursor.fetchall()
    assert 3 == len(rows)
    assert 3 == cursor.rowcount
    _close_db(cursor, cnx)

    assert [{'syncCount': 1, 'isCommitted': 0},
            {'syncCount': 2, 'isCommitted': 1},
            {'syncCount': 3, 'isCommitted': 0}] == rows


#########################################
## Test Mark Expired Session Committed ##
#########################################


def test_mark_expired_sessions_committed():
    """Test marking of expired past and future sessions as committed."""

    drop_create_tables()

    # Insert a Range of Expired and Current Session Rows #
    cursor, cnx, errno = open_db()
    assert None == errno

    # Insert sessions:
    # Expired Past  : -2 days, -1 hour 20 min.
    # Current       : -1 hour.
    # Expired Future: 1 day 20 min, 1 hour 20min.
    # Current       : 1 hour, now.
    statements = """INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', SUBTIME(NOW(),'48:00:00'));

                   INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', SUBTIME(NOW(),'01:20:01'));

                   INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', SUBTIME(NOW(),'01:00:01'));

                   INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', ADDTIME(NOW(),'24:20:01'));

                   INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', ADDTIME(NOW(),'01:20:01'));

                   INSERT INTO SyncCount (objectClass, createAt)
                   VALUES ('Product', ADDTIME(NOW(),'01:00:01'));

                   INSERT INTO SyncCount (objectClass)
                   VALUES ('Product');"""

    for result in cursor.execute(statements, multi=True):
        assert 1 == result.rowcount
        # Errors and warnings will raise.

    cnx.commit()
    _close_db(cursor, cnx)

    rowcount = mark_expired_sessions_committed_x(Product)

    # Assert Results #

    # Expired sessions marked committed.
    assert 4 == rowcount

    # Check rows.
    cursor, cnx, errno = open_db()
    assert None == errno
    statement = """SELECT syncCount, isCommitted FROM SyncCount ORDER BY syncCount"""
    cursor.execute(statement)
    rows = cursor.fetchall()
    assert 7 == len(rows)
    assert 7 == cursor.rowcount
    _close_db(cursor, cnx)

    assert [{'syncCount': 1, 'isCommitted': 1},
            {'syncCount': 2, 'isCommitted': 1},
            {'syncCount': 3, 'isCommitted': 0},
            {'syncCount': 4, 'isCommitted': 1},
            {'syncCount': 5, 'isCommitted': 1},
            {'syncCount': 6, 'isCommitted': 0},
            {'syncCount': 7, 'isCommitted': 0}] == rows


####################
## Test Sequences ##
####################


def test_session_sequence():
    """Test session sequence for a single object class."""

    drop_create_tables()

    compare_sc = get_committed_sc_x(Product)

    session_sc, committed_sc = session_sequence_x(Product)

    # Assert Result #
    assert compare_sc.sync_count + 1 == session_sc.sync_count
    assert committed_sc.sync_count == session_sc.sync_count


def test_session_sequence_repeating():
    """Test session sequence for a single object class, repeating."""

    drop_create_tables()

    def run():
        compare_sc = get_committed_sc_x(Product)

        session_sc, committed_sc = session_sequence_x(Product)

        # Assert Result #
        assert compare_sc.sync_count + 1 == session_sc.sync_count
        assert committed_sc.sync_count == session_sc.sync_count

    for i in range(5):
        run()

    statement = """SELECT syncCount, objectClass, isCommitted FROM SyncCount"""

    cursor, cnx, errno = open_db()
    assert None == errno
    cursor.execute(statement)
    rows = cursor.fetchall()

    # Assert Result #
    assert [{'syncCount': 5, 'objectClass': Product.__name__, 'isCommitted': 1}] == rows


def test_session_sequence_mixed_object_class():
    """Test session sequence for mixed object classes, repeating."""

    drop_create_tables()

    for i in range(5):
        session_sequence_x(Product)
        session_sequence_x(Setting)

    statement = """SELECT syncCount, objectClass, isCommitted FROM SyncCount"""

    cursor, cnx, errno = open_db()
    assert None == errno
    cursor.execute(statement)
    rows = cursor.fetchall()

    # Assert Result #
    assert [{'syncCount': 9, 'objectClass': Product.__name__, 'isCommitted': 1},
            {'syncCount': 10, 'objectClass': Setting.__name__, 'isCommitted': 1}] == rows


def test_get_session_sc_in_parallel_long_trailing_delete():
    """Parallel Sessions with long running trailing delete.

    Session a and b are run in new processes."""

    from multiprocessing import Process, Queue

    # client_id = new_client_id()
    new_client_id()

    def run_session_a(q):
        q.put('A Started')
        session_sc = get_session_sc_x(Product)
        q.put(session_sc)

        # Insert Object Class Rows #
        cursor, cnx, errno = open_db()
        assert None == errno

        # Simulate long running data transaction
        sleep(1)

        statement = """INSERT INTO Product (clientId, clientObjectId, lastSync, name)
                       VALUES (%s, %s, %s, %s)"""
        # session_sc.sync_count is used as clientObjectId for convenience.
        params = (1, session_sc.sync_count, session_sc.sync_count, 'session_a')
        cursor.execute(statement, params)
        cnx.commit()
        # Placed outside of commit to avoid queue lock, if any.
        q.put(cursor.lastrowid)
        _close_db(cursor, cnx)

    def run_session_b(q):
        q.put('B Started')
        session_sc = get_session_sc_x(Product)
        q.put(session_sc)

        # Insert Object Class Rows #
        cursor, cnx, errno = open_db()
        assert None == errno

        statement = """INSERT INTO Product (clientId, clientObjectId, lastSync, name)
                       VALUES (%s, %s, %s, %s)"""
        # session_sc.sync_count used as clientObjectId for convenience.
        params = (1, session_sc.sync_count, session_sc.sync_count, 'session_b')
        cursor.execute(statement, params)
        cnx.commit()
        # Placed outside of commit to avoid queue lock, if any.
        q.put(cursor.lastrowid)
        _close_db(cursor, cnx)

    a_queue = Queue()
    Process(target=run_session_a, args=(a_queue,)).start()
    assert 'A Started' == a_queue.get()  # blocking call

    b_queue = Queue()
    Process(target=run_session_b, args=(b_queue,)).start()
    assert 'B Started' == b_queue.get()  # blocking call

    # Session sync counts, a is issued before b.
    a_session_sc = a_queue.get()
    b_session_sc = b_queue.get()
    print 'a session_sc =', a_session_sc.sync_count
    print 'b session_sc =', b_session_sc.sync_count
    assert a_session_sc.sync_count < b_session_sc.sync_count

    # Product rowid, a is inserted after b.
    a_product_rowid = a_queue.get()
    b_product_rowid = b_queue.get()
    assert a_product_rowid > b_product_rowid


# def test_get_session_sc_in_parallel_long_data_transaction():
#         pass


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main(__file__)
