import re
 
test_str = "@charging_point / @area"

pattern = '@([a-zA-Z0-9_]+)'
params_list = re.findall(pattern, test_str)

print(params_list)