import mysql.connector
from os.path import realpath, isfile
from .bat import extract_anabat
import csv
from pandas import DataFrame
from .png_processing import *


def connect_to_db():
    conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                   passwd='batcalls-1', database='batechodata')
    db_info(conn)
    return conn


def conn_info():
    print('hostname: den1.mysql4.gear.host')
    print('username: batechodata')
    print('password: batcalls-1')
    print('database: batechodata')


def db_info(conn):
    # try-except block to handle any loss of connection to the database
    try:
        c = conn.cursor()
    except mysql.connector.errors.OperationalError:
        # reconnect to db and recreate executable cursor
        conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                           passwd='batcalls-1', database='batechodata')
        c = conn.cursor()

    c.execute('SELECT DATABASE();')

    curr_db = c.fetchall()[0][0]

    print('current database: {}'.format(curr_db))

    table_list(conn)


def table_list(conn):
    # try-except block to handle any loss of connection to the database
    try:
        c = conn.cursor()
    except mysql.connector.errors.OperationalError:
        # reconnect to db and recreate executable cursor
        conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                       passwd='batcalls-1', database='batechodata')
        c = conn.cursor()

    c.execute('SHOW TABLES;')

    temp = c.fetchall()
    tables = [temp[i][0] for i in range(0, len(temp))]

    print('tables: {}'.format(tables))


def create_table_file_path(conn, file_path):
    # get full (system-specific) file path if path contains ".."
    if '..' in file_path:
        file_path = realpath(file_path)

    # check whether path exists or leads to a file that exists; exit function if true
    if isfile(file_path) is False:
        print('File or file path does not exist in path {}'.format(file_path))
        return

    # get file name from path located after the last '\\' character
    file_name = file_path[file_path.rfind('\\') + 1:len(file_path)]

    if '-' in file_name:
        file_name = file_name.replace('-', '_')

    if '.' in file_name:
        file_name = file_name.replace('.', '$')

    sql_create_table = ''

    if file_path.endswith('csv'):
        # create_table_csv(conn, file_name, file_path)

        first_row = next(csv.reader(open(file_path)))

        columns = ''
        if len(first_row) == 3:
            columns = '(filename VARCHAR(255), time REAL, frequency REAL)'
        elif len(first_row) == 4:
            columns = '(filename VARCHAR(255), time REAL, frequency REAL, pulse INT)'

        sql_create_table = 'CREATE TABLE {} {};'.format(file_name, columns)
    elif file_path.endswith('#'):
        file_name = file_name.replace('#', 'zc')
        sql_create_table = 'CREATE TABLE {} (time REAL, frequency REAL);'.format(file_name)
    elif file_path.endswith('png'):
        sql_create_table = 'CREATE TABLE png_images (name VARCHAR(255), image BLOB NOT NULL);'
    else:
        print('Allowed files are csv, # (zero-crossing), and png')
        return

    # try-except block to handle any loss of connection to the database
    try:
        c = conn.cursor()
    except mysql.connector.errors.OperationalError:
        # reconnect to db and recreate executable cursor
        conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                       passwd='batcalls-1', database='batechodata')
        c = conn.cursor()

    try:
        c.execute(sql_create_table)
        table_list(conn)
    except mysql.connector.errors.ProgrammingError:
        print('Table {} already exists'.format(file_name))
        table_list(conn)

    print('Table {} has been successfully created'.format(file_name))

    if file_path.endswith('csv'):
        insert_into_table_csv(conn, file_name, file_path)
    elif file_path.endswith('#'):
        insert_into_table_zc(conn, file_name, file_path)
    elif file_path.endswith('png'):
        insert_into_table_png(conn, file_name, file_path)


def insert_into_table_csv(conn, table_name, file_path):
    # replace every "\\" (literal "\") in file_path with "\\\\" (literal "\\")
    file_path = file_path.replace('\\', '\\\\')

    sql_insert = 'LOAD DATA LOCAL INFILE \'{}\' INTO TABLE {} ' \
                                      'FIELDS TERMINATED BY \',\' LINES TERMINATED BY \'\\n\' IGNORE 1 LINES;' \
        .format(file_path, table_name)

    c = conn.cursor()
    c.execute(sql_insert)
    conn.commit()

    print(select_from_table(conn, table_name))


def insert_into_table_zc(conn, file_name, file_path):
    data = extract_anabat(file_path)

    time = data[0]
    freq = data[1]

    sql_insert = 'INSERT INTO {} VALUES (%s, %s);'.format(file_name)

    c = conn.cursor()

    for i in range(len(time)):
        c.execute(sql_insert, (float(time[i]), float(freq[i]),))
        conn.commit()

    # select_from_table(conn, table_name)


def insert_into_table_png(conn, file_name, file_path):
    # get a list of images that are already in the table png_images
    df = select_from_table(conn, 'png_images')
    img_lst = [df.loc[i]['name'] for i in range(df.shape[0])]

    # check whether image file_name already exists in the table
    if file_name in img_lst:
        print('Image {} already exists in png_images'.format(file_name))
    else:
        # encode image file into binary
        byte_array = encode_png_to_blob(file_path)

        # insert image into table
        c = conn.cursor()
        c.execute('INSERT INTO png_images VALUES (%s, %s);', (file_name, byte_array,))
        conn.commit()
        print('Image {} has been inserted into png_images'.format(file_name))

    print(select_from_table(conn, 'png_images'))


def drop_table(conn, table_name):
    # try-except block to handle any loss of connection to the database
    try:
        c = conn.cursor()
    except mysql.connector.errors.OperationalError:
        # reconnect to db and recreate executable cursor
        conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                       passwd='batcalls-1', database='batechodata')
        c = conn.cursor()

    sql_drop = 'DROP TABLE {};'.format(table_name)

    try:
        c.execute(sql_drop)
    except mysql.connector.errors.ProgrammingError:
        print('Table {} does not exist'.format(table_name))
        return

    print('Table {} has been successfully deleted from database'.format(table_name))
    table_list(conn)


def select_from_table(conn, table_name):
    # try-except block to handle any loss of connection to the database
    try:
        c = conn.cursor()
    except mysql.connector.errors.OperationalError:
        # reconnect to db and recreate executable cursor
        conn = mysql.connector.connect(host='den1.mysql4.gear.host', user='batechodata',
                                       passwd='batcalls-1', database='batechodata')
        c = conn.cursor()

    # set up SQL command for showing columns of table_name
    sql_show_columns = 'SHOW COLUMNS FROM {};'.format(table_name)

    # try_except block that checks whether table_name exists in db
    try:
        c.execute(sql_show_columns)
    except mysql.connector.errors.ProgrammingError:
        # let user know that table does not exist in db and exit function
        print('Table {} does not exist'.format(table_name))
        return

    # get the columns and put them into a list
    tmp = c.fetchall()
    columns = [tmp[i][0] for i in range(len(tmp))]

    # set up SQL command to show all of table_name
    sql_select = 'SELECT * FROM {};'.format(table_name)
    c.execute(sql_select)

    # create and return DataFrame representing the table
    return DataFrame.from_records(c.fetchall(), columns=columns)


def output_png_into_file(conn, img_name):
    # get DataFrame representation of table png_images
    df = select_from_table(conn, 'png_images')

    # reduce df to the (only) row containing img_name in "name" column
    df = df[df['name'] == img_name]

    # get byte data from "image" column of the acquired row of df
    byte_array = bytearray(df.loc[0]['image'])

    # call function to create a png file from retrieved byte data
    decode_blob_to_png(img_name, byte_array)
