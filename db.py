import psycopg2
import pymongo

class Querymethods():
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

    def execute_query(self, query):
        '''
        try to execute query in postgresql
        '''
        try: 
            conn = self.set_postgresql_connect()
            cur = conn.cursor()
            cur.execute(query)
            results = cur.fetchall()

        except Exception as e:
            print(e)
    
        return results

    def find_value(self, db_collection, field, value, filter_field):
        '''
        try to find the value for the requested field
        '''
        try:
            result = db_collection.find_one({field: value}, {filter_field: 1})
            return result

        except Exception as e:
            print(e)