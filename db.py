import psycopg2
import pymongo
from bson.json_util import dumps
import json

class Querymethods():
    def __init__(self):
        pass

    def set_postgresql_connect(self):
        '''
        try to connect postgresql, if error occurs, print it
        '''
        try:
            conn = psycopg2.connect("host=81.169.137.234 dbname=workbench user=david.reyer password=start_david")
        except Exception as e:
            print(e)

        return conn

    def set_mongodb_connect(self):
        '''
        try to connect mongodb, if error occurs, print it
        '''
        try:
            client = pymongo.MongoClient("localhost", 27017)

        except Exception as e:
            print(e)

        return client

    def execute_sqlquery(self, query):
        '''
        try to execute query in postgresql
        '''
        conn = self.set_postgresql_connect()
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
    
        return results

    def find_value(self, db_collection, field, value, filter_field):
        '''
        try to find the value for the requested field
        '''

        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]

        if collection:
            try:
                result = collection.find_one({field: value}, {filter_field: 1})
                return result

            except Exception as e:
                print(e)

    def insert_docu(self, db_collection, data):
        '''
        try to insert many documents at once

        data should be in the form:

        data = [
            {"_id": "101", "name": "Ram", "entries": ("26", "Hyderabad")},
            {"_id": "102", "name": "Rahim", "entries": ("27", "Bangalore")}
        ]
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            try:
                result = collection.insert_many(data)

            except Exception as e:
                print(e)

    def random_access(self, db_collection, num=1):
        '''
        try to access one random document from collction
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            try:
                results = collection.aggregate([{ "$sample": { "size": num } }])
                
                for result in results:
                    result = json.loads(dumps(result))
                    # print(result)
                    return result
            except Exception as e:
                print(e)

    def remove_docu(self, db_collection, docu_id):
        '''
        try to access one random document from collction
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            try:
                result = collection.delete_one({"_id": docu_id})
                print("remove", result)
            except Exception as e:
                print(e)

    def update_value(self, db_collection, field_1, field_2, old_value, new_value):
        '''
        try to update the value in a list given the field
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            try:
                result = collection.update({field_1:old_value},{"$push":{field_2:new_value}})
            except Exception as e:
                print(e)
        
make_query = Querymethods()
data = [
    {"name": "Ram", "entries": [["26", "Hyderabad"]]},
    {"name": "Rahim", "entries": [["27", "Bangalore"]]}
]
make_query.insert_docu("test",data)