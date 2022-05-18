import psycopg2
from constants import HOST, DBNAME, USER, PASSWORD

class Querymethods():
    def set_connect():
        '''
        try to connect the db, if error occurs, print it
        '''
        try:
            conn = psycopg2.connect("host=81.169.137.234 dbname=workbench user=david.reyer password=start_david")
        except Exception as e:
            print(e)

        return conn


