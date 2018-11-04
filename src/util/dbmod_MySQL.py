import mysql.connector

db_conn = mysql.connector.connect()
c = db_conn.cursor()


def connect_to_db(db_host, db_user, db_pwd):
    global db_conn
    try:
        db_conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            passwd=db_pwd
        )
    except:
        print('Unable to establish connection.'
              '\nPlease check whether service is running, then reconnect.')


def create_database(db_name):
    global c
    try:
        c.execute('CREATE DATABASE :database;',
                  {'database': db_name})
    except:
        print(f'Database \"{db_name}\" already exists.'
              '\nEither create one with a different name or modify this one.')


def create_table(tbl_name):
    global c
    try:
        c.execute('CREATE TABLE :table (time REAL, frequency REAL);',
                  {'table': tbl_name})
        print(f'Table \"{tbl_name}\" has been inserted successfully.')
        show_table()
    except:
        print(f'Table \"{tbl_name}\" already exists.'
              '\nEither create one with a different name or modify this one.')


def show_table():
    global c
    c.execute('SHOW TABLES;')
    print(c.fetchall())


def select_from_table(tbl_name):
    global c
    try:
        c.execute('SELECT * FROM :table',
                  {'table': tbl_name})
    except:
        print(f'Table {tbl_name} does not exist in current database.'
              '\nEither create this table of select from a different table.')


def insert_into_table(tbl_name, time_val, frequency_val):
    global db_conn, c
    with db_conn:
        c.execute('INSERT INTO :table VALUES (:x, :y)',
                  {'x': time_val, 'y': frequency_val})
    select_from_table(tbl_name)