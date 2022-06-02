import re
from typing import List
from rapidfuzz.process import extractOne, extract
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity
from rapidfuzz.fuzz import ratio
from db import Querymethods
from typing import Text, List, Optional, Union, Any, Dict, Set

class ResolveKPIDefinition():

    '''
    this class processes user-defined KPI. 

    '''

    def __init__(self, kpi, place, time):
        self.kpi = kpi
        self.place = place
        self.time = time

    def parammeter_extraction(self) -> List:
        # use regex for extraction
        # return a list containing all found parts
        pattern = '@([a-zA-Z0-9_]+)'
        params_list = re.findall(pattern, self.KPI_definition)
        return params_list


    def argument_filling(self, params) -> List[Dict[Text, Any]]:
        # return the value for each argument in a dictionary

        with open('../lookup/Predefined_KPI.txt', 'r', encoding='utf8') as f:
            data = f.read()
            predefined_kpi = data.split('\n')

        for param in params:
            if param in predefined_kpi:
                translator = QueryTranslator()
                is_prediction = translator.kpi_is_prediction(DATE)
                q, place, time = translator.agg_query(kpi, place, DATE, max=max, min=min, avg=avg)

            results = Querymethods.execute_query(q)

                
                # execute in postgresql

            else:
                # execute in mongodb    
            
            
        return args_list

    def arithmetic(self):
        pass

    def output(self):
        pass