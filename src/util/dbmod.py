"""
Module for accessing and modifying database (currently a file)
Requires a csv file to parse into database
"""

import sqlite3, csv

# database.db -> persistent database file
conn = sqlite3.connect('database.db')
c = conn.cursor()

def create_table(file_name, r):
    with conn:
        c.execute("CREATE TABLE " + file_name + " (time REAL, frequency REAL);")

        # insert points into table
        for line in r:
            c.execute("INSERT INTO " + file_name + " VALUES (:x, :y);", {
                'x': line[0], # time column
                'y': line[1]  # frequency column
            })

def show_table(file_name):
    c.execute("SELECT * FROM " + file_name + ";")
    return c.fetchall()

def get_no_of_rows(file_name):
    c.execute("SELECT COUNT(*) FROM " + file_name + ";")
    return c.fetchone()[0]

def drop_table(file_name):
    with conn:
        c.execute("DROP TABLE " + file_name + ";")

# function to delete points, useful for cleaning up the data
def delete_point(file_name, x, y):
    with conn:
        c.execute("DELETE FROM " + file_name + " WHERE time = :x AND frequency = :y;", {'x': x, 'y': y})