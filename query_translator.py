from ast import Pass
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
            'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value}=(SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\') AND month={mapped_time};",
            'template5': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value}=(SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\') AND month={mapped_time};",
            'template6': f"SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';", 
            'template7': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};",
            'template8': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time}) AND month={mapped_time};",
            'template9': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time}) AND month={mapped_time};",
            'template10': f"SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};",
            'template11': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC LIMIT 1;", 
            'template12': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC LIMIT 1;",
            'template13': f"SELECT SUM(no_total_chargepoints)/(SUM(total_traffic)/1000) AS chargepoints_per_1000cars, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state;",
            'template14': f"SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state;",
            'template15': f"SELECT SUM(no_total_chargepoints)/(SUM(total_traffic)/1000) AS chargepoints_per_1000cars, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state ORDER BY chargepoints_per_1000cars DESC LIMIT 1;",
            'template16': f"SELECT SUM(no_total_chargepoints)/(SUM(total_traffic)/1000) AS chargepoints_per_1000cars, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state ORDER BY chargepoints_per_1000cars ASC LIMIT 1;",
            'template17': f"SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoints, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state ORDER BY cars_per_chargepoint DESC LIMIT 1;",
            'template18': f"SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state ORDER BY cars_per_chargepoint ASC LIMIT 1;",
            'template19': f"SELECT AVG(chargepoints_per_1000cars) FROM (SELECT sum(no_total_chargepoints)*1000/sum(total_traffic) AS chargepoints_per_1000cars FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state) t;",
            'template20': f"SELECT AVG(cars_per_chargepoint) FROM (SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time} GROUP BY T1.state) t;",
            'template21': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state;",
            'template22': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state ORDER BY p_o_t DESC LIMIT 1;",
            'template23': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state ORDER BY p_o_t ASC LIMIT 1;",
            'template24': f"SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t;",
            # 'template25': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';",
            # 'template26': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS cars_per_chargepoint FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';"
            # 'template27': f""
        }

        if kpi in ("Cars_per_charging_point", "Charging_points_per_1,000_cars", "Percentage_of_target") and "state" in place.lower():
            if kpi == "Cars_per_charging_point":
                if avg:
                    selected_template = templates['template20']
                elif max:
                    selected_template = templates['template17']
                elif min:
                    selected_template = templates['template18']
                else:
                    selected_template = templates['template14']
            elif kpi == "Charging_points_per_1,000_cars":
                if avg:
                    selected_template = templates['template19']
                elif max:
                    selected_template = templates['template15']
                elif min:
                    selected_template = templates['template16']
                else:
                    selected_template = templates['template13']
            elif kpi == "Percentage_of_target":
                if avg:
                    selected_template = templates['template24']
                elif max:
                    selected_template = templates['template22']
                elif min:
                    selected_template = templates['template23']
                else:
                    selected_template = templates['template21']
        else:
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
            elif "state" in place.lower():
                if avg: 
                    selected_template = templates['template10']
                elif max:
                    selected_template = templates['template11']
                elif min:
                    selected_template = templates['template12']
            elif place.lower() in ("county", "counties"):
                if avg:
                    selected_template = templates['template7']
                elif max:
                    selected_template = templates['template8']
                elif min:
                    selected_template = templates['template9']
            else:
                selected_template = templates['template6']

        return selected_template, place, mapped_time

    def group_sort_query(self, kpi, place, time, desc=None, asc=None, max=None, min=None):
        mapped_time = self.time_mapping(time)
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;", 
            'template3': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;",
            'template4': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;",
            'template5': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;",
            'template6': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;",
            'template7': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;",
            'template8': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;",
            'template9': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;",
            'template10': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state;",
            'template11': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state DESC;",
            'template12': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state ASC;",
        }

        if kpi == "Cars_per_charging_point":
            if desc is None and asc is None:
                selected_template = templates['template4']
            elif desc:
                selected_template = templates['template5']
            elif asc:
                selected_template = templates['template6']
        elif kpi == "Charging_points_per_1,000_cars":
            if desc is None and asc is None:
                selected_template = templates['template7']
            elif desc:
                selected_template = templates['template8']
            elif asc:
                selected_template = templates['template9']
        elif kpi == "Percentage_of_target":
            if desc is None and asc is None:
                selected_template = templates['template10']
            elif desc:
                selected_template = templates['template11']
            elif asc:
                selected_template = templates['template12']
        else:
            if desc is None and asc is None:
                selected_template = templates['template1']
            elif desc:
                selected_template = templates['template2']
            elif asc:
                selected_template = templates['template3']
        
        return selected_template, place, mapped_time


    def filter_query(self, kpi, place, time, ge=None, le=None, bet=None, CARDINAL=None):
        mapped_time = self.time_mapping(time)
        kpi_value = self.kpi_mapping(kpi)
        number_l = None
        number_r = None
        if ge:
            symbol = '>='
            # number = ge.split()[-1]
        elif le:
            symbol = '<='
            # number = le.split()[-1]
        elif bet:
            number_l = bet.split()[1]
            number_r = bet.split()[-1]

        templates = {
            'template1': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} > (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template2': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} < (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});", 
            'template3': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} > {number_l} AND {kpi_value} < {number_r};",
            'template4': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi_value} {symbol} {CARDINAL};",
            'template5': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template6': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) < (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});",
            'template7': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > {number_l} AND SUM({kpi_value}) < {number_r};",
            'template8': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) {symbol} {CARDINAL};",           
            'template9': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) >(SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template10': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) <(SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template11': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) >(SELECT AVG(traffic_chargepoint) FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template12': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) <(SELECT AVG(traffic_chargepoint) FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template13': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) >(SELECT AVG(chargepoints_per_1000cars) FROM (SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template14': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) <(SELECT AVG(chargepoints_per_1000cars) FROM (SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state) t);",
            'template15': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) {symbol} {CARDINAL};",
            'template16': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) > {number_l} AND SUM(traffic)/SUM(no_total_chargepoints) < {number_r};",
            'template17': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) {symbol} {CARDINAL};",
            'template18': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) > {number_l} AND SUM(no_total_chargepoints)/(SUM(traffic)/1000) < {number_r};",            
            'template19': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) {symbol} {CARDINAL};",
            'template20': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) > {number_l} AND 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) < {number_r};"
       }


        
        if "state" in place.lower():
            if kpi in ("Locations", "Charging_stations", "Charging_points"):
                if ge == "above average" or ge == "over average" or ge == "more than average":
                    selected_template = templates['template5']
                elif le == "below average" or le == "under average":
                    selected_template = templates['template6']
                elif bet:
                    selected_template = templates['template7']
                elif le or ge:                
                    selected_template = templates['template8']
            elif kpi == "Cars_per_charging_point":
                if ge == "above average" or ge == "over average" or ge == "more than average":
                    selected_template = templates['template11']
                elif le == "below average" or le == "under average":
                    selected_template = templates['template12']
                elif bet:
                    selected_template = templates['template16']
                elif le or ge:                
                    selected_template = templates['template15']
            elif kpi == "Charging_points_per_1,000_cars":
                if ge == "above average" or ge == "over average" or ge == "more than average":
                    selected_template = templates['template13']
                elif le == "below average" or le == "under average":
                    selected_template = templates['template14']
                elif bet:
                    selected_template = templates['template18']
                elif le or ge:                
                    selected_template = templates['template17']
            elif kpi == "Percentage_of_target":
                if ge == "above average" or ge == "over average" or ge == "more than average":
                    selected_template = templates['template9']
                elif le == "below average" or le == "under average":
                    selected_template = templates['template10']
                elif bet:
                    selected_template = templates['template20']
                elif le or ge:                
                    selected_template = templates['template19']                                

        else:
            if ge == "above average" or ge == "over average" or ge == "more than average":
                selected_template = templates['template1']
            elif le == "below average" or le == "under average":
                selected_template = templates['template2']
            elif bet:
                selected_template = templates['template3']
            elif le or ge:
                selected_template = templates['template4']
        
        return selected_template, place, mapped_time

    def limit_query(self, kpi, place, time, CARDINAL, top, bottom):
        mapped_time = self.time_mapping(time)
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum Limit {CARDINAL};",
            'template3': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} ORDER BY {kpi_value} DESC Limit {CARDINAL};",
            'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} ORDER BY {kpi_value} Limit {CARDINAL};",
            'template5': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY traffic_chargepoint DESC Limit {CARDINAL};",
            'template6': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY traffic_chargepoint Limit {CARDINAL};",
            'template7': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY chargepoints_per_1000cars DESC Limit {CARDINAL};",
            'template8': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY chargepoints_per_1000cars Limit {CARDINAL};",
            'template9': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY p_o_t DESC Limit {CARDINAL};",
            'template10': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY p_o_t Limit {CARDINAL};",
        }

        # check if it is top or below
        if "state" in place.lower():
            if kpi in ("Locations", "Charging_stations", "Charging_points"):
                if top:
                    selected_template = templates['template1']
                elif bottom:
                    selected_template = templates['template2']
                else:
                    selected_template = templates['template1']
            elif kpi == "Cars_per_charging_point":
                if top:
                    selected_template = templates['template5']
                elif bottom:
                    selected_template = templates['template6']
                else:
                    selected_template = templates['template5']   
            elif kpi == "Charging_points_per_1,000_cars":
                if top:
                    selected_template = templates['template7']
                elif bottom:
                    selected_template = templates['template8']
                else:
                    selected_template = templates['template7']
            elif kpi == "Percentage_of_target":
                if top:
                    selected_template = templates['template9']
                elif bottom:
                    selected_template = templates['template10']
                else:
                    selected_template = templates['template9']                                          
        else:
            if top:
                selected_template = templates['template3']
            elif bottom:
                selected_template = templates['template4']
            else:
                selected_template = templates['template3']
        
        return selected_template, place, mapped_time

    # def window_query(self, kpi, time, place, place_list=None):
    #     mapped_time = self.time_mapping(time)
    #     kpi_value = self.kpi_mapping(kpi)


    #     if place_list:
    #         place_value = ""
    #         place_list = place_list.split(",")
    #         for element in place_list:
    #             element = element.strip()
    #             place_value += element
    #         place_value = "("+place_value+")"
    #     elif place:
    #         place_value = place

    #     templates = {
    #         'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state IN {place_value} GROUP BY state;"
    #     }
        
    #     return templates['template1']