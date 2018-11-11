"""
GearHost MySQL server login credentials:
- host: den1.mysql4.gear.host
- username: batechodata
- password: batcalls-1
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


def create_database(db_name):
    global db_cursor

    """ Python 3 """
    try:
        db_cursor.execute(f'CREATE DATABASE {db_name};')
    except mysql.connector.errors.ProgrammingError:
        print(f'Database \"{db_name}\" already exists.')

    """ Python 2 """
    # try:
    #     db_cursor.execute('CREATE DATABASE {};'.format(db_name))
    # except mysql.connector.errors.ProgrammingError:
    #     print('Database \"{}\" already exists.'.format(db_name))


def access_database(db_name):
    global hostname, username, password, db_tables, curr_db
    connect_to_db(hostname, username, password, db_name)
    get_tables_from_db(curr_db)


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

    """ Python 3 """
    db_cursor.execute(f'CREATE TABLE {tbl_name} (time REAL, frequency REAL);')
    print(f'Table \"{tbl_name}\" has been created successfully.')

    """ Python 2 """
    # db_cursor.execute('CREATE TABLE {} (time REAL, frequency REAL);'.format(tbl_name))
    # print('Table {} has been created successfully.'.format(tbl_name))

    get_tables_from_db(curr_db)


def drop_table(tbl_name):
    global db_cursor, db_tables

    """ Python 3 """
    try:
        db_cursor.execute(f'DROP TABLE {tbl_name};')
        print(f'Table \"{tbl_name}\" has been removed successfully.')
        db_tables.remove(tbl_name)
    except mysql.connector.errors.ProgrammingError:
        print(f'Table {tbl_name} does not exist in current database')

    """ Python 2 """
    # try:
    #     db_cursor.execute('DROP TABLE {};'.format(tbl_name))
    #     print('Table \"{}\" has been removed successfully.'.format(tbl_name))
    #     db_tables.remove(tbl_name)
    # except mysql.connector.errors.ProgrammingError:
    #     print('Table {tbl_name} does not exist in current database'.format(tbl_name))


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

    """ Python 3 """
    try:
        db_cursor.execute(f'SELECT * FROM {tbl_name}')
    except mysql.connector.errors.ProgrammingError:
        print(f'Table {tbl_name} does not exist in current database.')

    """ Python 2 """
    # try:
    #     db_cursor.execute('SELECT FROM {};'.format(tbl_name))
    # except mysql.connector.errors.ProgrammingError:
    #     print('Table {} does not exist in current database.'.format(tbl_name))


"""
Below function insert_into_table() inserts values into a 2-column table according to current create_table() function.
Will be changed if create_table() has a dynamic number of columns.
"""


# below function inserts values into a 2-column table
def insert_into_table(tbl_name, val_1, val_2):
    global db_connection, db_cursor

    """ Python 3 """
    sql = f'INSERT INTO {tbl_name} VALUES (%s, %s);'

    """ Python 2 """
    # sql = 'INSERT INTO {} VALUES (%s, %s);'.format(tbl_name)

    db_cursor.execute(sql, (val_1, val_2,))
    db_connection.commit()


def delete_value_from_table(tbl_name, val_1, val_2):
    global db_connection, db_cursor

    """ Python 3 """
    sql = f'DELETE FROM {tbl_name} WHERE time = %s AND frequency = %s;'

    """ Python 2 """
    # sql = 'DELETE FROM {} WHERE time = %s AND frequency = %s;'.format(tbl_name)

    db_cursor.execute(sql, (val_1, val_2,))

    db_connection.commit()


def get_no_of_rows(tbl_name):
    global db_cursor

    """ Python 3 """
    try:
        db_cursor.execute(f'SELECT COUNT(*) FROM {tbl_name};')
    except mysql.connector.errors.ProgrammingError:
        print(f'Table {tbl_name} does not exist in current database.')

    """ Python 2 """
    # try:
    #     db_cursor.execute('SELECT COUNT(*) FROM {}'.format(tbl_name))
    # except mysql.connector.errors.ProgrammingError:
    #     print('Table {} does not exist in current database.'.format(tbl_name))