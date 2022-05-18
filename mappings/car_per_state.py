import sys
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)

from db_connection import Querymethods

conn = Querymethods.set_connect()
cur = conn.cursor()

q = "SELECT sum(total_traffic), state FROM \"E-Mobility\".kfz_per_county GROUP BY state;"
cur.execute(q)
results = cur.fetchall()
print(results)
# car_per_state_dict = {}
# car_per_chargepoint = 
# chargepoint_per_1000car = {}

# for result in results:
#     car_per_state_dict[result[1]] = result[0]

# q = "SELECT SUM(no_total_chargepoints), state FROM \"E-Mobility\".emo_historical WHERE month=202201 GROUP BY state;"
# cur.execute(q)
# results = cur.fetchall()

# for result in results:
#     car_num = car_per_state_dict[result[1]]
#     car_per_state_dict[result[1]] = round(car_num/result[0])

# print(car_per_state_dict)