"""
Module for accessing and modifying database (MongoDB cloud server)
Requires a csv file to parse into database
"""

import csv
import pymongo as pm
import pprint

# establish connection to cloud server
# password is omitted for presentation
client = pm.MongoClient(
    "mongodb+srv://csc505g7:<PASSWORD>@bat-echolocation-data-sthaf.mongodb.net/test?retryWrites=true")

# create new database
db = client.bat_call_db

# create a new collection
collection = db.bat_call

# function to create documents (i.e. tables)
def create_document(csv_file_name, reader):

    # put data into a single document
    doc = {
        "name": csv_file_name,
        "time": [line[0] for line in reader],
        "freq": [line[1] for line in reader]
    }

    # insert document into db
    doc_id = collection.insert_one(doc).inserted_id

    # return id of document
    return doc_id

# function to output new document
def show_document(id):
    pprint.pprint(collection.find_one({"_id": id}))

# function to obtain a document (can store in variable)
def get_document(id):
    return collection.find_one({"_id": id})

def delete_document(id):
    collection.delete_one({"_id": id})

def update_document(new_doc, old_doc_id):
    collection.replace_one({"_id": old_doc_id}, new_doc)