import mysql.connector
from os.path import realpath, isfile
from .bat import extract_anabat
import csv
from .png_processing import *


def connect_to_db():
    conn = mysql.connector.connect(
        host='den1.mysql4.gear.host', user='batechodata', passwd='batcalls-1', database='batechodata')

    # try:
    #     conn = mysql.connector.connect(
    #         host='den1.mysql4.gear.host', user='batechodata', passwd='batcalls-1', database='batechodata')
    # except mysql.connector.errors.InterfaceError:
    #     # error with hostname and/or whether service is online
    #     print('Unable to establish connection - check whether the server is online '
    #           'and whether the hostname is correct, then reconnect.')
    # except mysql.connector.errors.ProgrammingError:
    #     # error w/ one or a combination of username, pwd, and database name
    #     print('Unable to verify credentials and/or database name - '
    #           'please correct any errors in either field before reconnecting.')

    db_info(conn)
    return conn


def db_info(conn):
    c = conn.cursor()

    try:
        c.execute('SELECT DATABASE();')
    except mysql.connector.errors.InterfaceError:
        # connection to database lost after a certain period of time
        conn = connect_to_db()
        c = conn.cursor()
        c.execute('SELECT DATABASE();')

    curr_db = c.fetchall()[0][0]

    print('current database: {}'.format(curr_db))

    # Python 3 version of above print statement
    # print(f'current database: {curr_db}')

    table_list(conn)


def table_list(conn):
    c = conn.cursor()

    try:
        c.execute('SHOW TABLES;')
    except mysql.connector.errors.InterfaceError:
        # connection to database lost after a certain period of time
        conn = connect_to_db()
        c = conn.cursor()
        c.execute('SHOW TABLES;')

    temp = c.fetchall()
    tables = [temp[i][0] for i in range(0, len(temp))]

    print('tables: {}'.format(tables))


def create_table_from_file_path(conn, file_path):
    print('file directory: {}'.format(file_path))

    # get while directory if dot directory
    if '..' in file_path:
        whole_file_path = realpath(file_path)
        print('new file path: {}'.format(whole_file_path))

    if isfile(whole_file_path) is False:
        print('File or file path does not exist in path {}'.format(whole_file_path))
        return

    # get file name from directory located after the last '\\' character
    file_name = whole_file_path[whole_file_path.rfind('\\')+1:len(whole_file_path)]
    print('file name: {}'.format(file_name))

    # get data name from file name without 4-character file extension (.csv, .(int)(int)#, or .png)
    data_name = file_name[0:-4]
    print('data name: {}'.format(data_name))

    if file_name.endswith('csv'):
        f_ext = 'csv'
        if data_name.endswith('#'):
            print('data {} contains zc/# extension'.format(data_name))
            data_name = data_name[:-4]
            print('new data name: {}'.format(data_name))

        reader = csv.reader(open(whole_file_path))
        first_row = next(reader)

        if len(first_row) == 4:
            columns = '(filename VARCHAR(12), time REAL, frequency REAL, pulse INT)'
        elif len(first_row) == 3:
            columns = '(filename VARCHAR(12), time REAL, frequency REAL)'
    elif file_name.endswith('png'):
        print('file type: png')
        f_ext = 'png'
        columns = '(x INT, y INT)'

        if '.' in data_name:
            data_name = data_name.replace('.', '_')

        if '#' in data_name:
            data_name = data_name.replace('#', '')

        # print(f'new data name: {data_name}')
    elif file_name.endswith('#'):
        print('file type: zc/#')
        f_ext = 'zc'
        columns = '(time REAL, frequency REAL)'

    data_name = '{}_{}'.format(data_name, f_ext)

    sql_create_table = 'CREATE TABLE {} {};'.format(data_name, columns)

    # print('SQL command: {}'.format(sql_create_table))

    c = conn.cursor()

    try:
        c.execute(sql_create_table)
    except mysql.connector.errors.InterfaceError:
        # connection to database lost after a certain period of time
        conn = connect_to_db()
        c = conn.cursor()
        c.execute(sql_create_table)
    except mysql.connector.errors.ProgrammingError:
        print('Table {} already exists'.format(data_name))
        return

    table_list(conn)

    """
    streamlined create-insert functionality: upon creating a table, immediately insert values into said table from file
    """
    if file_name.endswith('csv'):
        insert_into_table_csv(conn, data_name, whole_file_path)
    elif file_name.endswith('png'):
        insert_into_table_png(conn, data_name, whole_file_path)
    elif file_name.endswith('#'):
        insert_into_table_zc(conn, data_name, whole_file_path)


def insert_into_table_csv(conn, table_name, file_path):
    # passing a file path into SQL requires '\\\\' (literal '\\') rather than '\\" (literal '\')
    file_path = file_path.replace('\\', '\\\\')
    # print(f'new whole file directory: {file_directory}')

    sql_insert = 'LOAD DATA LOCAL INFILE \'{}\' INTO TABLE {} ' \
                                      'FIELDS TERMINATED BY \',\' LINES TERMINATED BY \'\\n\' IGNORE 1 LINES;' \
        .format(file_path, table_name)

    # print('SQL command: {}'.format(sql_insert))

    c = conn.cursor()
    c.execute(sql_insert)
    conn.commit()

    # select_from_table(conn, table_name)


def insert_into_table_png(conn, table_name, file_path):
    x, y = extract_png(file_path)

    # for i in range(len(x)):
    #     print(f'{x[i]}\t{y[i]}')

    sql_insert = 'INSERT INTO {} VALUES (%s, %s)'.format(table_name)

    # print(sql_insert)

    c = conn.cursor()

    for i in range(len(x)):
        # print(i)
        c.execute(sql_insert, (x[i], y[i]))
        conn.commit()

    # select_from_table(conn, table_name)


def insert_into_table_zc(conn, table_name, file_path):
    data = extract_anabat(file_path)

    time = data[0]
    freq = data[1]

    sql_insert = 'INSERT INTO {} VALUES (%s, %s);'.format(table_name)

    # Python 3 version of above declaration
    # sql_insert = f'INSERT INTO {table_name} VALUES (%s, %s);'

    c = conn.cursor()

    for i in range(len(time)):
        c.execute(sql_insert, (float(time[i]), float(freq[i]),))
        conn.commit()

    # select_from_table(conn, table_name)


def drop_table(conn, table_name):
    c = conn.cursor()

    sql_drop = 'DROP TABLE {};'.format(table_name)

    try:
        c.execute(sql_drop)
    except mysql.connector.errors.InterfaceError:
        # connection to database lost after a certain period of time
        conn = connect_to_db()
        c = conn.cursor()
        c.execute(sql_drop)
    except mysql.connector.errors.ProgrammingError:
        print('Table {} does not exist'.format(table_name))
        return

    table_list(conn)


def select_from_table(conn, table_name):
    c = conn.cursor()

    sql_select = 'SELECT * FROM {};'.format(table_name)

    try:
        c.execute(sql_select)
    except mysql.connector.errors.InterfaceError:
        # connection to database lost after a certain period of time
        conn = connect_to_db()
        c = conn.cursor()
        c.execute(sql_select)
    except mysql.connector.errors.ProgrammingError:
        print('Table {} does not exist'.format(table_name))
        return

    output = c.fetchall()

    print('table {}:'.format(table_name))

    for i in range(len(output)):
        print(output[i])

    return output


"""
GearHost MySQL server login credentials:
- host: den1.mysql4.gear.host
- username: batechodata
- password: batcalls-1
"""
