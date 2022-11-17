import psycopg2
import pymongo
from bson.json_util import dumps
import json
from bson import BSON
from bson.objectid import ObjectId

class Querymethods():
    def __init__(self):
        pass

    def set_postgresql_connect(self):
        '''
        connect postgresql.

        container port is default to 5432
        '''
        local_conn_str = "host=81.169.137.234 dbname=workbench user=david.reyer password=start_david"
        docker_conn_str = "host=192.168.1.100 dbname=workbench user=david.reyer password=start_david"

        conn = psycopg2.connect(docker_conn_str)

        return conn

    def set_mongodb_connect(self):
        '''
        connect mongodb
        '''

        client = pymongo.MongoClient("192.168.1.100", 27017)

        return client

    def execute_sqlquery(self, query):
        '''
        execute query in postgresql
        '''
        conn = self.set_postgresql_connect()
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
    
        return results

    def find_value(self, db_collection, field, value, filter_field):
        '''
        find the value for the requested field
        '''

        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]

        if collection:
            result = collection.find_one({field: value}, {filter_field: 1})
            return result


    def insert_docu(self, db_collection, data):
        '''
        insert many documents at once

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
            result = collection.insert_many(data)


    def random_access(self, db_collection, num=1):
        '''
        try to access one random document from collction
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            results = collection.aggregate([{ "$sample": { "size": num } }])
            
            for result in results:
                result = json.loads(dumps(result))
                result['_id'] = result['_id']['$oid']

                return result

    def remove_docu(self, db_collection, docu_id):
        '''
        access one random document from collction
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]

        if collection:
            result = collection.delete_one({"_id": ObjectId(docu_id)})



    def update_value(self, db_collection, field_1, field_2, old_value, new_value):
        '''
        update the value in a list given the field
        '''
        client = self.set_mongodb_connect()
        db = client["emobility"]
        collection = db[db_collection]
        if collection:
            result = collection.update({field_1:old_value},{"$push":{field_2:new_value}})

    # @staticmethod 
    # def get_docu_id(docu):
    #     # util function for 'action_quiz_finished'
    #     return ObjectId(docu["_id"]['$oid'])
        
# make_query = Querymethods()
# data = [
#     {"name": "Ram", "entries": [["26", "Hyderabad"]]},
#     {"name": "Rahim", "entries": [["27", "Bangalore"]]}
# ]
# make_query.insert_docu("test",data)