"""
The following code will require a local MySQL server to be currently running on your machine,
otherwise it will trigger an OperationalError when importing this module.
This can be done with either Wampserver for Windows systems, MAMP for macOS systems, or LAMP for Linux systems.
Just have the MySQL server running when you have either one of them installed to avoid any errors.

Then, when the above is done, you should have your preset hostname as localhost and username as root,
with the password initialized as blank. Use these login credentials for the connect_to_db() function.

Currently, I am looking for an SQL-based database cloud server that I can set up without having to pay for usage
to avoid all of us having to do the above. I will modify the code accordingly, if need be.

Also, I will be testing this code in the db_kevin Jupyter notebook using sample data.

-- Kevin :)
"""

import mysql.connector

hostname, username, password = None, None, None
db_connection, db_cursor = None, None
curr_db = None
db_tables = None


def connect_to_db(db_host, db_user, db_pwd, db_name):
    global hostname, username, password
    global db_connection, db_cursor
    global curr_db, db_tables

    try:
        db_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            passwd=db_pwd
        )
        hostname, username, password = db_host, db_user, db_pwd

        db_cursor = db_connection.cursor()

        if db_name is not None:
            curr_db = db_name
            db_connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                passwd=db_pwd,
                database=db_name
            )
            db_cursor = db_connection.cursor()

            """ Python 3 """
            print(f'Database access granted - current database is {curr_db}')

            """ Python 2 """
            # print('Database access granted - current database is {}'.format(curr_db))

        server_info()
    except mysql.connector.errors.InterfaceError:
        # error with hostname and/or whether service is online
        print('Unable to establish connection - check whether the status is online '
              'and whether the hostname is correct, then reconnect.')
    except mysql.connector.errors.ProgrammingError:
        # error w/ one or a combination of username, pwd, and database name
        print('Unable to verify credentials and/or database name - '
              'please correct any errors in either field before reconnecting.')


def server_info():
    global curr_db, db_tables

    """ Python 3 """
    print(f'Current database: {curr_db}\nCurrent tables in {curr_db}: {db_tables}')

    """ Python 2 """
    # print('Current database: {}\nCurrent tables in {}: {}'.format(curr_db, curr_db, db_tables))


def switch_database(db_name):
    global db_cursor
    try:
        db_cursor.execute('CREATE DATABASE %s;', (db_name,))
    except mysql.connector.errors.ProgrammingError:
        """ Python 3 """
        print(f'Database \"{db_name}\" already exists.')

        """ Python 2 """
        # print('Database \"{}\" already exists.'.format(db_name))


def access_database(db_name):
    global hostname, username, password, db_tables, curr_db
    connect_to_db(hostname, username, password, db_name)
    get_tables_from_db(curr_db)


def drop_table(tbl_name):
    global db_cursor, db_tables

    try:
        db_cursor.execute('DROP TABLE %s;', (tbl_name,))
        db_tables.remove(tbl_name)
    except mysql.connector.errors.ProgrammingError:
        """ Python 3 """
        print(f'Table {tbl_name} does not exist in current database')

        """ Python 2 """
        # print('Table {tbl_name} does not exist in current database'.format(tbl_name))


"""
According to Hadi, the data is essentially a set of points, each having corresponding x and y values; 
x represents the time values, and y represents the frequency values. 
The following create_table() function will create a new table with two columns: one for the x values, 
and another for the y values. I am considering including another column for cluster identification for a later version.

I'm debating on whether to create a table with dynamic number of columns rather than hard-coding just 2 (or 3) columns.
As of the moment I'll settle on the latter.
"""


def create_table(tbl_name):
    global curr_db

    db_cursor.execute('CREATE TABLE %s (time REAL, frequency REAL);', (tbl_name,))

    """ Python 3 """
    print(f'Table \"{tbl_name}\" has been created successfully.')

    """ Python 2 """
    # print('Table \"%s\" has been created successfully.', (tbl_name,))

    get_tables_from_db(curr_db)


def get_tables_from_db(db_name):
    global db_cursor, db_tables

    db_cursor.execute('SHOW TABLES;')
    tmp = db_cursor.fetchall()
    db_tables = [tmp[i][0] for i in range(0, len(tmp))]

    """ Python 3 """
    print(f'Current tables in {db_name}: {db_tables}')

    """ Python 2 """
    # print('Current tables in {}: {}'.format(db_name, db_tables))


"""
Debating whether to keep this function:

def show_tables():
    global db_tables
    print('Current tables: %s', (db_tables,))
"""


def show_specific_table(tbl_name):
    global db_cursor
    try:
        db_cursor.execute('SELECT * FROM %s', (tbl_name,))
    except mysql.connector.errors.ProgrammingError:
        """ Python 3 """
        print(f'Table {tbl_name} does not exist in current database.')

        """ Python 2 """
        # print('Table {} does not exist in current database.'.format(tbl_name))


"""
Below function insert_into_table() inserts values into a 2-column table according to current create_table() function.
Will be changed if create_table() has a dynamic number of columns.
"""


# below function inserts values into a 2-column table
def insert_into_table(tbl_name, val_1, val_2):
    global db_connection, db_cursor

    db_cursor.execute('INSERT INTO %s VALUES (%s, %s);', (tbl_name, val_1, val_2,))
    db_connection.commit()


def get_no_of_rows(tbl_name):
    global db_cursor
    try:
        db_cursor.execute('SELECT COUNT(*) FROM %s;', (tbl_name,))
        # db_cursor.execute('SELECT COUNT(*) FROM :table;', {'table': tbl_name})
    except mysql.connector.errors.ProgrammingError:
        """ Python 3 """
        print(f'Table {tbl_name} does not exist in current database.')

        """ Python 2 """
        print('Table %s does not exist in current database.'.format(tbl_name))
