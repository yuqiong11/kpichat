from lib2to3.pytree import convert
import re
from typing import List
from rapidfuzz.process import extractOne, extract
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity
from rapidfuzz.fuzz import ratio
from db import Querymethods
from typing import Text, List, Optional, Union, Any, Dict, Set

from utils.constants import PREDEFINED_KPI
from utils.stack import ConvertMathFormular
from query_translator import QueryTranslator
import sys
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/lookup'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
from mappings.synonym_mapping import PREDEFINED_KPI_MAPPING, predefined_kpi_mapping
from mappings.time_mapping import CheckTime

# from New_KPI import new_kpi_list

from collections import deque

class ResolveKPIDefinition():

    '''
    this class processes user-defined KPI. 

    '''

    def __init__(self):
        pass

    def parameter_extraction(self, my_string) -> List:
        # use regex for extraction
        # return a list containing all found parts
        pattern = '@([a-zA-Z0-9_]+)'
        params_list = re.findall(pattern, my_string)
        print('params_list', params_list)
        return params_list


    def argument_filling(self, params, place, DATE) -> Dict[Text, Any]:
        # return the value for each argument in a dictionary

        # with open('../lookup/Predefined_KPI.txt', 'r', encoding='utf8') as f:
        #     data = f.read()
        #     predefined_kpi = data.split('\n')
        # time mapping
        map_time = CheckTime()
        time = map_time.time_mapping(DATE[0], False)

        args_dict = {}
        args_to_be_asked = []

        make_query = Querymethods()

        for param in params:
            mapped_param = predefined_kpi_mapping(PREDEFINED_KPI_MAPPING, param)
            if mapped_param in PREDEFINED_KPI:
                # execute in postgresql
                translator = QueryTranslator()
                q = translator.agg_query(mapped_param, place, DATE)
                print('q ', q)

                result = make_query.execute_sqlquery(q[0])

                # add into dictionary
                args_dict[param] = round(result[0][0])

                continue

            # execute in mongodb
            # check if the param is in the knowledgebase 'statistics'. If not, ask the user for missing information
            # [(500, 'Berlin', '202207'), (600, 'Hamburg', '202207')]
            results_name = make_query.find_value("statistics", "name", param, "entries")

            if results_name:
                print("process_newKPI line 80: found statistics in mongodb.")
                # param is in the database
                # for example, 'area' is there, but 'Berlin' has no entry under it
                found = False
                for entry in results_name["entries"]:
                    if entry[1] == place[0] and entry[2] == time:
                        result = entry[0]
                        # add into dictionary
                        args_dict[param] = result
                        found = True
                        break 
                if not found:
                    # information not in the database                            
                    args_to_be_asked.append(param) 
                    print("information not in the database")
                       
            else: 
                # param is not in the database
                # 'area' is not there, so there is no entry
                
                args_to_be_asked.append(param)
                print("param is not in the database")

            # code stops above, the following is not being used for now ################################
            # check if the param is a userdefined kpi
            # elif param in new_kpi_list:
            #     # execute in mongodb
            #     results_definition = make_query.find_value("new_kpi_definition", "kpi_name", param, "kpi_definition")

            #     if results_definition:
            #         # resolve kpi definiton
            #         pass

                    
        return args_dict, args_to_be_asked

    def formular_filling(self, formular, args_dict):
        # fill a math formular with numbers
        # (@my_param + @my_param_1/@param)* -> (5+6/3)*2
        for k, v in args_dict.items():
            formular = formular.replace('@'+k, str(v))
            print("formular", formular)

        return formular

    def arithmetic(self, formular, args_dict):
        # calculate 
        convertor = ConvertMathFormular()
        filled_formular = self.formular_filling(formular, args_dict)
        tokens = convertor.get_tokens(filled_formular)
        result = convertor.main_func(tokens)
        return result

    # def output(self):
    #     pass


my_string = '@charging_station/@population'
pattern = '@([a-zA-Z0-9_]+)'
print(re.findall(pattern, my_string))