# importing the psycopg2 module
import psycopg2
# connecting to the database
conn = psycopg2.connect("host=81.169.137.234 dbname=workbench user=david.reyer password=start_david")
# Open a cursor to perform database operations
cur = conn.cursor()
# cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
# cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)",(100, "abc'def"))
cur.execute("SELECT no_total_locations FROM \"E-Mobility\".emo_historical WHERE month=202112; ")
'print("result:", result)'
result=cur.fetchall()
print(len(result))
if len(result) == 1:
    print(result[0][0])
# Make the changes to the database persistent
# conn.commit()
# Close communication with the database
# cur.close()
# conn.close()