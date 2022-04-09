import sys
from sklearn.feature_selection import SelectFromModel

from torch import q_per_channel_axis, q_per_channel_zero_points
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)
from kpi_mapping import KPI_MAPPING
from time_mapping import CheckTime
from constants import STATE_LIST

class QueryTranslator(CheckTime):
    def __init__(self):
        pass

    def kpi_mapping(self,kpi):
        return KPI_MAPPING[kpi]


    # def allocator(self, intent):
    #     allocation_references = {
    #         "agg_query": self.agg_query(),
    #         "group_sort_query": self.group_sort_query(),
    #         "filter_query": self.filter_query(),
    #         "limit_query": self.limit_query(),
    #         "window_query": self.window_query()
    #     }
    #     return allocation_references[intent]
    
    def agg_query(self,kpi, place, time, max=None, min=None, avg=None):
        mapped_time = self.time_mapping(time)
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};",
            'template2': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';",
            'template3': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';",
            'template4': f"SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';",
            'template5': f"SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';",
            'template6': f"SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';", 
            'template7': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};",
            'template8': f"SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};", 
            'template9': f"SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};",
            'template10': f"SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};"
        }

        if place.lower() == "germany":
            selected_template = templates['template1']
        elif place in STATE_LIST:
            if avg:
                selected_template = templates['template3']
            elif max:
                selected_template = templates['template4']
            elif min:
                selected_template = templates['template5']
            else:
                selected_template = templates['template2']
        elif place.lower() in ("state", "states", "federal state", "federal states"):
            if avg: 
                selected_template = templates['template10']
        elif place.lower() in ("county", "counties"):
            if avg:
                selected_template = templates['template7']
            elif max:
                selected_template = templates['template8']
            elif min:
                selected_template = templates['template9']
        else:
            selected_template = templates['template6']

        return selected_template

    def group_sort_query(self, kpi, place, time, desc=None, asc=None):
        mapped_time = self.time_mapping()
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;", 
            'template3': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;", 
        }

        if desc == None and asc == None:
            selected_template = templates['template1']
        elif desc != None:
            selected_template = templates['template2']
        elif asc != None:
            selected_template = templates['template3']
        
        return selected_template


    def filter_query(self, kpi, place, time, user_input, ge=None, le=None, bet=None):
        mapped_time = self.time_mapping()
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} > (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template2': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} < (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});", 
            'template3': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} > {number_l} AND {kpi_value} < {number_r};",
            'template4': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} {symbol} {number};",
            'template5': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template6': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) < (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template7': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > {number_l} AND SUM({kpi_value}) < {number_r};",
            'template8': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) {symbol} {number};",           
        }
        if place.lower() in STATE_LIST:
            if "abover average" or "over average" in user_input:
                selected_template = templates['template5']
            elif "below average" or "under average" in user_input:
                selected_template = templates['template6']
            elif bet:
                selected_template = templates['template7']
            elif le or ge:
                selected_template = templates['template8']
        else:
            if "abover average" or "over average" in user_input:
                selected_template = templates['template1']
            elif "below average" or "under average" in user_input:
                selected_template = templates['template2']
            elif bet:
                selected_template = templates['template3']
            elif le or ge:
                selected_template = templates['template4']
        
        return selected_template

    def limit_query(self, kpi, place, time, user_input, CARDINAL):
        mapped_time = self.time_mapping()
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum Limit {CARDINAL};"
        }

        # check if it is top or below
        if "top" in user_input:
            selected_template = templates['template1']
        elif "below" or "last" in user_input:
            selected_template = templates['template2']
        
        return selected_template

    def window_query(self, kpi, time, place):
        mapped_time = self.time_mapping()
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state IN {place} GROUP BY state;"
        }


        
        return templates['template1']