"""
The following code will require a local MySQL server to be currently running on your machine,
otherwise it will trigger an OperationalError when importing this module.
This can be done with either Wampserver for Windows systems, MAMP for macOS systems, or LAMP for Linux systems.
Just have the MySQL server running when you have either one of them installed.

Then, when the above is done, you should have your preset hostname as localhost and username as root,
with the password initialized as blank. Use these login credentials for the connect_to_db() function.

Currently, I am looking for an SQL-based database cloud server that I can set up without having to pay for usage
to avoid all of us having to do the above. I will modify the code accordingly, if need be.

Also, I will be testing this code in the db_kevin Jupyter notebook using sample data.

-- Kevin :)
"""

import mysql.connector

db_conn = None
c = None

"""
START: code to be evaluated later
"""


def connect_to_db(db_host, db_user, db_pwd, db_name):
    global db_conn, c
    try:
        if db_name is not None:
            db_conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                passwd=db_pwd,
                database = db_name
            )
        else:
            db_conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                passwd=db_pwd
            )

        c = db_conn.cursor()

    except:
        print('Unable to establish connection.'
              '\nPlease check whether service is running, then reconnect.')


def create_database(db_name):
    global db_conn, c
    try:
        c.execute('CREATE DATABASE :database;',
                  {'database': db_name})
    except:
        print(f'Database \"{db_name}\" already exists.'
              '\nEither create one with a different name or modify this one.')


"""
END: code to be evaluated later
"""

"""
According to Hadi, the data is essentially a set of points, each having corresponding x and y values; 
x represents the time values, and y represents the frequency values. 
The following create_table() function will create a new table with two columns: one for the x values, 
and another for the y values. I am considering including another column for cluster identification for a later version.
"""


def create_table(tbl_name):
    global c
    try:
        c.execute('CREATE TABLE :table (time REAL, frequency REAL);',
                  {'table': tbl_name})
        print(f'Table \"{tbl_name}\" has been created successfully.')
        show_tables()
    except:
        print(f'Table \"{tbl_name}\" already exists.'
              '\nEither create one with a different name or modify this one.')


def show_tables():
    global c
    c.execute('SHOW TABLES;')
    tmp = c.fetchall()
    tables = [c.fetchall()[i][0] for i in range(0, len(c.fetchall()))]
    print(tables)


def select_from_table(tbl_name):
    global c
    try:
        c.execute('SELECT * FROM :table',
                  {'table': tbl_name})
    except:
        print(f'Table {tbl_name} does not exist in current database.'
              '\nEither create this table or select from a different table.')


def insert_into_table(tbl_name, time_val, frequency_val):
    global db_conn, c
    with db_conn:
        c.execute('INSERT INTO :table VALUES (:x, :y)',
                  {'x': time_val, 'y': frequency_val})
    select_from_table(tbl_name)


def get_no_of_rows(tbl_name):
    global c
    try:
        c.execute('SELECT COUNT(*) FROM :table;',
                  {'table': tbl_name})
    except:
        print(f'Table {tbl_name} does not exist in current database.'
              '\nEither create this table or select from a different table.')


def aggregate(tbl_name, tbl_col, agg_func):
    global c

    print(tbl_name)
    select_from_table(tbl_name)

    c.execute('SHOW COLUMNS FROM :table;',
              {'table': tbl_name})
    tmp = c.fetchall()
    col_lst = [tmp[i][0] for i in range(0, len(tmp))]
    if tbl_col not in col_lst:
        print(f'Invalid option - please select a column in {tbl_name}')

    if agg_func not in ['avg', 'min', 'max', 'sum', 'count']:
        print('Invalid aggregation function')

    c.execute('SELECT :function(:column) FROM :table;')
    return c.fetchall()

    # sql_cmd = ''

    # ipt_1 = input('Select an aggregate function:'
    #             '\n1: avg'
    #             '\n2: min'
    #             '\n3: max'
    #             '\n4: sum'
    #             '\n5: count'
    #             '\n')

    # while ipt_1 not in ['1', '2', '3', '4', '5',
    #                   'average', 'min', 'max', 'sum', 'count']:
    #     ipt_1 = input('Not a valid option - please try again.\n')
    #
    # ipt_2 = input('Select ')

    # if ipt in ['1', 'avg']:
    #     ipt = input('Select a column:'
    #                 '\n1: \"x\" or \"time\"'
    #                 '\n2: \"y\" or \"freq\" or \"frequency\"')
    #
    #     while ipt not in ['1', '2', 'x', 'y', 'time', 'freq', 'frequency']:
    #         ipt = input('Not a valid option - please try again.\n')
    #
    #     if ipt in ['1', 'x', 'time']:
    #         sql_cmd = 'SELECT avg()'
    #
    #     if ipt in ['1', '2', 'x', 'y', 'time', 'freq', 'frequency']:
    #         sql_cmd = f'SELECT avg({tbl_col}) FROM {tbl_name}'
    #     elif ipt == '*':
    #         sql_cmd = f'SELECT'
    #
    # elif ipt in ['2', 'min']:
    #     print('option 2: min')
    # elif ipt in ['3', 'max']:
    #     print('option 3: max')
    # elif ipt in ['4', 'sum']:
    #     print('option 4: sum')
    # elif ipt in ['5', 'count']:
    #     print('option 5: count')