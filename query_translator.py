from ast import Pass
from msilib.schema import Error
import sys
from regex import E
from sklearn.feature_selection import SelectFromModel

from torch import q_per_channel_axis, q_per_channel_zero_points
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)
from kpi_mapping import KPI_MAPPING
from charger_type_mapping import CHARGER_TYPE_MAPPING
from time_mapping import CheckTime
from constants import STATE_LIST

class QueryTranslator(CheckTime):
    def __init__(self):
        pass

    def kpi_mapping(self,kpi):
        return KPI_MAPPING[kpi]

    def charger_type_mapping(self, charger_type):
        return CHARGER_TYPE_MAPPING[charger_type]

    # def allocator(self, intent):
    #     allocation_references = {
    #         "agg_query": self.agg_query(),
    #         "group_sort_query": self.group_sort_query(),
    #         "filter_query": self.filter_query(),
    #         "limit_query": self.limit_query(),
    #         "window_query": self.window_query()
    #     }
    #     return allocation_references[intent]
    
    def agg_query(self,kpi, place, time, max=None, min=None, avg=None, increase=None):
        # place
        if len(place) == 1:
            place_1 = None
        if len(place) == 2:
            place_1 = place[1]
        # time mapping
        mapped_time_start, mapped_time_end = None, None
        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False), self.time_mapping(time_end, False)


        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",
            'template2': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\';",
            'template3': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state =\'{place[0]}\';",
            'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value}=(SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0] if place[0] in STATE_LIST else place_1}\') AND month={mapped_time_start};",
            'template5': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value}=(SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0] if place[0] in STATE_LIST else place_1}\') AND month={mapped_time_start};",
            'template6': f"SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place[0]}%\';", 
            'template7': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",
            'template8': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AND month={mapped_time_start};",
            'template9': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AND month={mapped_time_start};",
            'template10': f"SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",
            'template11': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC LIMIT 1;", 
            'template12': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum ASC LIMIT 1;",
            'template13': f"SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = 'Bayern';",
            'template14': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\';",
            'template15': f"SELECT SUM(no_total_chargepoints)/(SUM(total_traffic)/1000) AS chargepoints_per_1000cars, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state ORDER BY chargepoints_per_1000cars DESC LIMIT 1;",
            'template16': f"SELECT SUM(no_total_chargepoints)/(SUM(total_traffic)/1000) AS chargepoints_per_1000cars, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state ORDER BY chargepoints_per_1000cars ASC LIMIT 1;",
            'template17': f"SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoints, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state ORDER BY cars_per_chargepoint DESC LIMIT 1;",
            'template18': f"SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint, T1.state FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state ORDER BY cars_per_chargepoint ASC LIMIT 1;",
            'template19': f"SELECT AVG(chargepoints_per_1000cars) FROM (SELECT sum(no_total_chargepoints)*1000/sum(total_traffic) AS chargepoints_per_1000cars FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state) t;",
            'template20': f"SELECT AVG(cars_per_chargepoint) FROM (SELECT SUM(total_traffic)/SUM(no_total_chargepoints) AS cars_per_chargepoint FROM \"E-Mobility\".kfz_per_county T1 JOIN \"E-Mobility\".emo_historical T2 ON T1.regionalschlussel = T2.regionalschlussel WHERE month={mapped_time_start} GROUP BY T1.state) t;",
            'template21': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} AND state=\'{place[0]}\';",
            'template22': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state ORDER BY p_o_t DESC LIMIT 1;",
            'template23': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state ORDER BY p_o_t ASC LIMIT 1;",
            'template24': f"SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t;",
           
           
           
            'template25': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') AS difference;",
            'template26': f"SELECT (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND county LIKE \'%{place[0]}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place[0]}%\') AS difference;",
            'template27': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",
            'template28': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",
            'template29': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference DESC LIMIT 1;",
            'template30': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference ASC LIMIT 1;",       
            'template31': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference DESC LIMIT 1;",
            'template32': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference ASC LIMIT 1;",
            'template33': f"SELECT (SELECT SUM({kpi_value})/COUNT(county) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) - (SELECT SUM({kpi_value})/COUNT(county) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",
            'template34': f"SELECT (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) - (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",
            'template35': f"SELECT AVG(t1.kpi - t2.kpi) AS avg_difference FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county;",


          
            'template36': f"SELECT (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state = \'{place[0]}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            'template37': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",
            'template38': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",        
          
          
            'template39': f"SELECT (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') AS difference;",
            'template40': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",            
            'template41': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",     

            'template42': f"SELECT (SELECT SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state = \'{place[0]}\') - (SELECT SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            'template43': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",
            'template44': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",        

            'template45': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start if mapped_time_end else ''}) AS difference;"
        }
        # incase there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if increase:
            print('increased')
            # template 25-44
            # queries about increase
            if place[0].lower() in ("germany","deutschland"):
                selected_template.append(templates['template45'])
            elif place[0] in STATE_LIST:
                if kpi in ("Cars_per_charging_point", "", "Percentage_of_target"):
                    if kpi == "Cars_per_charging_point":
                        selected_template.append(templates['template42'])
                    elif kpi == "Charging_points_per_1000_cars":
                        selected_template.append(templates['template36'])
                    elif kpi == "Percentage_of_target":
                        selected_template.append(templates['template39'])
                else:
                    selected_template.append(templates['template25'])

            elif max and "state" in place[0].lower():
                if kpi == "Cars_per_charging_point":
                    selected_template.append(templates['template43'])
                elif kpi == "Charging_points_per_1000_cars":
                    selected_template.append(templates['template37'])
                elif kpi == "Percentage_of_target":
                    selected_template.append(templates['template40'])
                else:
                    # percentage as additional info
                    selected_template.append(templates['template27'])
                    # selected_template.append(templates['template2'])
            elif min and "state" in place[0].lower():
                if kpi == "Cars_per_charging_point":
                    selected_template.append(templates['template44'])
                elif kpi == "Charging_points_per_1000_cars":
                    selected_template.append(templates['template38'])
                elif kpi == "Percentage_of_target":
                    selected_template.append(templates['template41'])
                else:
                    selected_template.append(templates['template28'])
            elif max and len(place) == 2 and "count" in (place[0].lower(),place[1].lower()):
                selected_template.append(templates['template31'])
            elif min and len(place) == 2 and "count" in (place[0].lower(), place[1].lower()):
                selected_template.append(templates['template32'])
            elif max and len(place) == 1 and "count" in place[0].lower():
                selected_template.append(templates['template29'])
            elif min and len(place) == 1 and "count" in place[0].lower():
                selected_template.append(templates['template30'])
            elif avg and "state" in place[0].lower():
                selected_template.append(templates['template34'])   
            elif avg and "count" in place[0].lower():
                selected_template.append(templates['template33'])
            elif avg and "germany" in place[0].lower():
                selected_template.append(templates['template33'])
            elif avg and len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
                selected_template.append(templates['template35'])  
            else:
                print('about to append..')
                # queires about a specific county
                # no list, so it is put here under 'else'
                # percentage as additional info
                selected_template.append(templates['template26'])
                selected_template.append(templates['template6'])
        else:
            # template 1-24
            # queries not about increase
            if kpi in ("Cars_per_charging_point", "", "Percentage_of_target") and "state" in place[0].lower():
                if kpi == "Cars_per_charging_point":
                    if avg:
                        selected_template.append(templates['template20'])
                    elif max:
                        selected_template.append(templates['template17'])
                    elif min:
                        selected_template.append(templates['template18'])
                    else:
                        selected_template.append(templates['template14'])
                elif kpi == "Charging_points_per_1000_cars":
                    if avg:
                        selected_template.append(templates['template19'])
                    elif max:
                        selected_template.append(templates['template15'])
                    elif min:
                        selected_template.append(templates['template16'])
                    else:
                        selected_template.append(templates['template13'])
                elif kpi == "Percentage_of_target":
                    if avg:
                        selected_template.append(templates['template24'])
                    elif max:
                        selected_template.append(templates['template22'])
                    elif min:
                        selected_template.append(templates['template23'])
                    else:
                        selected_template.append(templates['template21'])
            else:
                if place[0].lower() in ("germany", "deutschland"):
                    selected_template.append(templates['template1'])
                    selected_template.append(templates['template1'])
                elif (place[0] in STATE_LIST) or (len(place) == 2 and place[0].lower() in ("county", "counties")):
                    if avg:
                        selected_template.append(templates['template3'])
                    elif max:
                        # percentage as additional info
                        selected_template.append(templates['template4'])
                        selected_template.append(templates['template1'])
                    elif min:
                        # percentage as additional info
                        selected_template.append(templates['template5'])
                        selected_template.append(templates['template1'])
                    else:
                        # percentage as additional info
                        selected_template.append(templates['template2'])
                        selected_template.append(templates['template1'])
                elif "state" in place[0].lower():
                    if avg: 
                        selected_template.append(templates['template10'])
                    elif max:
                        selected_template.append(templates['template11'])
                        selected_template.append(templates['template1'])
                    elif min:
                        selected_template.append(templates['template12'])
                        selected_template.append(templates['template1'])
                elif len(place) == 1 and place[0].lower() in ("county", "counties"):
                    if avg:
                        selected_template.append(templates['template7'])
                    elif max:
                        selected_template.append(templates['template8'])
                        selected_template.append(templates['template1'])
                    elif min:
                        selected_template.append(templates['template9'])
                        selected_template.append(templates['template1'])
                elif len(place) == 2 and place[0].lower() in ("county", "counties"):
                    if avg:
                        selected_template.append(templates['template3'])
                    elif max:
                        selected_template.append(templates['template4'])
                        selected_template.append(templates['template1'])
                    elif min:
                        selected_template.append(templates['template5'])
                        selected_template.append(templates['template1'])                       
                else:
                    # percentage as additional info
                    selected_template.append(templates['template6'])
                    selected_template.append(templates['template1'])

        return selected_template

    def charger_type_query(self, place, charger_type, max=None, min=None, avg=None):
        # questions 
        # fast/normal chargers in berlin/sachsen/Germany
        # max/min fast/normal chargers in berlin/sachsen
        # avg of fast/normal chargers of a county of sachsen/ a county/ a state

        # charger type mapping
        c_type = self.charger_type_mapping(charger_type)
        # place
        if len(place) == 1:
            place_1 = None
        if len(place) == 2:
            place_1 = place[1]
        '''
            'template1': f"fast/normal in germany",
            'template2': f"fast/normal in berlin",
            'template3': f"fast/normal in sachsen",
            'template4': f"county with max of fast/normal",
            'template5': f"county with min of fast/normal",
            'template6': f"state with max of fast/normal",
            'template7': f"state with min of fast/normal",
            'template8': f"avg of fast/normal of a county",
            'template9': f"avg of fast/normal of a state",
            'template10': f"avg of fast/normal of a county in sachsen"
            'template11': f"county in a state with max of fast/normal"
            'template12':f"county in a state with min of fast/normal"
        '''
        templates = {
            'template1': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\';",
            'template2': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' AND landkreis LIKE \'%{place[0]}%\';",
            'template3': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' AND bundesland = \'{place[0]}\';",
            'template4': f"SELECT landkreis, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' GROUP BY landkreis ORDER BY count DESC LIMIT 1;",
            'template5': f"SELECT landkreis, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' GROUP BY landkreis ORDER BY count ASC LIMIT 1;",
            'template6': f"SELECT bundesland, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' GROUP BY bundesland ORDER BY count DESC LIMIT 1;",
            'template7': f"SELECT bundesland, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' GROUP BY bundesland ORDER BY count ASC LIMIT 1;",
            'template8': f"SELECT COUNT(*)/COUNT(DISTINCT(landkreis)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\';",
            'template9': f"SELECT COUNT(*)/COUNT(DISTINCT(bundesland)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\';",
            'template10': f"SELECT AVG(count) FROM (SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' AND bundesland = \'{place[0]}\' GROUP BY landkreis) AS t;",
            'template11': f"SELECT COUNT(*), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' AND bundesland = \'{place_1}\' GROUP BY landkreis ORDER BY count DESC LIMIT 1;",
            'template12': f"SELECT COUNT(*), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{c_type}\' AND bundesland = \'{place_1}\' GROUP BY landkreis ORDER BY count ASC LIMIT 1;"
        }
        # in case there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        # template 1-12
        if len(place) ==1 and place[0].lower() == "germany":
            selected_template.append(templates['template1'])
        elif len(place)==1 and place[0] in STATE_LIST:
            if max:
                # percentage as additional info
                selected_template.append(templates['template4'])
                selected_template.append(templates['template1'])
            elif min:
                # percentage as additional info
                selected_template.append(templates['template5'])
                selected_template.append(templates['template1'])
            else:
                selected_template.append(templates['template3'])
                selected_template.append(templates['template1'])
        elif len(place) ==1 and "state" in place[0].lower():
            if avg: 
                selected_template.append(templates['template9'])
            elif max:
                selected_template.append(templates['template6'])
                selected_template.append(templates['template1'])
            elif min:
                selected_template.append(templates['template7'])
                selected_template.append(templates['template1'])
        elif len(place) ==1 and place[0].lower() in ("county", "counties"):
            if avg:
                selected_template.append(templates['template8'])
            elif max:
                selected_template.append(templates['template4'])
                selected_template.append(templates['template1'])
            elif min:
                selected_template.append(templates['template5'])
                selected_template.append(templates['template1'])
        elif len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
            if avg:
                selected_template.append(templates['template10'])
            elif max:
                selected_template.append(templates['template11'])
                selected_template.append(templates['template1'])
            elif min:
                selected_template.append(templates['template12'])
                selected_template.append(templates['template1'])
        else:
            # percentage as additional info
            selected_template.append(templates['template2'])
            selected_template.append(templates['template1'])

        return selected_template

    def charger_operator_query(self, place, max=None, min=None):
        # questions
        # measures how many charging points do each operator have in total
        # what kind of operators are there in berlin/sachsen/Germany 
        # strongest/weakest operators in berlin/sachsen/Germany
        # place
        if len(place) == 1:
            place_1 = None
        if len(place) == 2:
            place_1 = place[1]
        '''
            'template1': f"operators in germany",
            'template2': f"operators in berlin",
            'template3': f"operators in sachsen",
            'template4': f"strongest operators of germany",
            'template5': f"strongest operators of berlin",
            'template6': f"strongest operators of sachsen",
            'template7': f"weakest operators of germany",
            'template8': f"weakest operators of berlin",
            'template9': f"weakest operators of sachsen"
            'template10: f"total number of charging point"
        '''
        templates = {
            'template1': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source GROUP BY betreiber ORDER BY number DESC;",
            'template2': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE landkreis LIKE \'%{place[0]}%\' GROUP BY betreiber ORDER BY number DESC;",
            'template3': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE bundesland = \'{place[0]}\' GROUP BY betreiber ORDER BY number DESC;",
            'template4': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            'template5': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE landkreis LIKE \'%{place[0]}%\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            'template6': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE bundesland = \'{place[0]}\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            'template7': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source GROUP BY betreiber ORDER BY number ASC LIMIT 1;",
            'template8': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE landkreis LIKE \'%{place[0]}%\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",
            'template9': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE bundesland = \'{place[0]}\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",
            'template10': f"SELECT SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source;"
        }
        # in case there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        # template 1-10
        if place[0].lower() == "germany":
            if max: 
                selected_template.append(templates['template4'])
                selected_template.append(templates['template10'])
            elif min: 
                selected_template.append(templates['template7'])
                selected_template.append(templates['template10'])   
            else:
                selected_template.append(templates['template1'])
                selected_template.append(templates['template10'])             
        elif place[0] in STATE_LIST:
            if max: 
                selected_template.append(templates['template6'])
                selected_template.append(templates['template10'])
            elif min: 
                selected_template.append(templates['template9'])
                selected_template.append(templates['template10'])   
            else:
                selected_template.append(templates['template3'])
                selected_template.append(templates['template10'])  
        else:
            if max: 
                selected_template.append(templates['template5'])
                selected_template.append(templates['template10'])
            elif min: 
                selected_template.append(templates['template8'])
                selected_template.append(templates['template10'])   
            else:
                selected_template.append(templates['template2'])
                selected_template.append(templates['template10'])  

        return selected_template



    def group_sort_query(self, kpi, time, desc=None, asc=None, max=None, min=None, increase=None):
        # time mapping
        mapped_time_start, mapped_time_end = None, None
        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False), self.time_mapping(time_end, False)
        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state;",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC;", 
            'template3': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum ASC;",
            'template4': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state;",
            'template5': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC;",
            'template6': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum ASC;",
            'template7': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state;",
            'template8': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC;",
            'template9': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum ASC;",
            'template10': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state;",
            'template11': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state DESC;",
            'template12': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state ASC;",

            'template14': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY t1.state;",
            'template15': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC;",
            'template16': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC;",
            'template17': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY t1.state;",
            'template18': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC;",
            'template19': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC;",
            'template20': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY t1.state;",
            'template21': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC;",
            'template22': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC;",
            'template23': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ORDER BY t1.state;",            
            'template24': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC;",
            'template25': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC;",
        }

        # incase there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if kpi == "Cars_per_charging_point":
            if increase:
                if desc is None and asc is None:
                    selected_template.append(templates['template20'])
                elif desc:
                    selected_template.append(templates['template21'])
                elif asc:
                    selected_template.append(templates['template22'])
            else:
                if desc is None and asc is None:
                    selected_template.append(templates['template4'])
                elif desc:
                    selected_template.append(templates['template5'])
                elif asc:
                    selected_template.append(templates['template6'])
        elif kpi == "Charging_points_per_1000_cars":
            if increase:
                if desc is None and asc is None:
                    selected_template.append(templates['template14'])
                elif desc:
                    selected_template.append(templates['template15'])
                elif asc:
                    selected_template.append(templates['template16'])               
            else:
                if desc is None and asc is None:
                    selected_template.append(templates['template7'])
                elif desc:
                    selected_template.append(templates['template8'])
                elif asc:
                    selected_template.append(templates['template9'])
        elif kpi == "Percentage_of_target":
            if increase:
                if desc is None and asc is None:
                    selected_template.append(templates['template17'])
                elif desc:
                    selected_template.append(templates['template18'])
                elif asc:
                    selected_template.append(templates['template19'])                
            else:
                if desc is None and asc is None:
                    selected_template.append(templates['template10'])
                elif desc:
                    selected_template.append(templates['template11'])
                elif asc:
                    selected_template.append(templates['template12'])
        else:
            if increase:
                if desc is None and asc is None:
                    selected_template.append(templates['template23'])
                elif desc:
                    selected_template.append(templates['template24'])
                elif asc:
                    selected_template.append(templates['template25'])
            else: 
                if desc is None and asc is None:
                    selected_template.append(templates['template1'])
                elif desc:
                    selected_template.append(templates['template2'])
                elif asc:
                    selected_template.append(templates['template3'])
        
        return selected_template


    def filter_query(self, kpi, place, time, ge=None, le=None, bet=None, CARDINAL=None, increase=None):
        # place
        if len(place) == 1:
            place_1 = None
        if len(place) == 2:
            place_1 = place[1]
        # time mapping
        mapped_time_start, mapped_time_end = None, None
        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False), self.time_mapping(time_end, False)
        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)

        # operator mapping
        if ge:
            symbol = '>='
        elif le:
            symbol = '<='

        # CARDINAL mapping
        number_0, number_1 = None, None
        if len(CARDINAL) == 2:
            number_0, number_1 = CARDINAL[0], CARDINAL[1]
            if '%' in number_0:
                number_0 = number_0.replace('%', '')
                # number_0 = float(number_0)/100
            if '%' in number_1:
                number_1 = number_1.replace('%', '')
                # number_1 = float(number_1)/100         
        else:
            number_0 = CARDINAL[0]
            if '%' in number_0:
                number_0 = number_0.replace('%', '')
                # number_0 = float(number_0)/100


        templates = {
            'template1': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} > (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) ORDER BY Percentage_of_target DESC;",
            'template2': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} < (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) ORDER BY Percentage_of_target DESC;", 
            'template3': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} > {number_0} AND {kpi_value} < {number_1} ORDER BY Percentage_of_target DESC;",
            'template4': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} {symbol} {number_0} ORDER BY Percentage_of_target DESC;",
            'template5': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state HAVING SUM({kpi_value}) > (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) ORDER BY sum DESC;",
            'template6': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state HAVING SUM({kpi_value}) < (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) ORDER BY sum DESC;",
            'template7': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state HAVING SUM({kpi_value}) > {number_0} AND SUM({kpi_value}) < {number_1} ORDER BY sum DESC;",
            'template8': f"SELECT state, SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state HAVING SUM({kpi_value}) {symbol} {number_0} ORDER BY sum DESC;",           
            'template9': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) >(SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template10': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) <(SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template11': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) >(SELECT AVG(traffic_chargepoint) FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template12': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) <(SELECT AVG(traffic_chargepoint) FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template13': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) >(SELECT AVG(chargepoints_per_1000cars) FROM (SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template14': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) <(SELECT AVG(chargepoints_per_1000cars) FROM (SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t);",
            'template15': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) {symbol} {number_0};",
            'template16': f"SELECT state, SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(traffic)/SUM(no_total_chargepoints) > {number_0} AND SUM(traffic)/SUM(no_total_chargepoints) < {number_1};",
            'template17': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) {symbol} {number_0};",
            'template18': f"SELECT state, SUM(no_total_chargepoints)/(SUM(traffic)/1000) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING SUM(no_total_chargepoints)/(SUM(traffic)/1000) > {number_0} AND SUM(no_total_chargepoints)/(SUM(traffic)/1000) < {number_1};",            
            'template19': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) {symbol} {number_0};",
            'template20': f"SELECT state, 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state HAVING 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) > {number_0} AND 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) < {number_1};",
            'template21': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') AS difference;",
            'template22': f"SELECT (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND county LIKE \'%{place[0]}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place[0]}%\') AS difference;",
            'template23': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference DESC;",
            'template24': f"SELECT * FROM (SELECT t1.county, t1.kpi - t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference DESC;",
            'template25': f"SELECT (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state = \'{place[0]}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            'template26': f"SELECT (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') AS difference;",            
            'template27': f"SELECT (SELECT SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state = \'{place[0]}\') - (SELECT SUM(traffic)/SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            'template28': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference DESC;",
            'template29': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference;",
            'template30': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference;",
            'template31': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference;",
            'template32': f"SELECT * FROM (SELECT t1.county, t1.kpi - t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference DESC;",
            'template33': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference;",
            'template34': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference;",
            'template35': f"SELECT * FROM (SELECT t1.state, t1.kpi - t2.kpi AS difference FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference;",
            'template36': f"SELECT * FROM (SELECT t1.county, t1.kpi - t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference DESC;",
            'template37': f"SELECT * FROM (SELECT t1.county, t1.kpi - t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference DESC;",
            'template38': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\' AND {kpi_value} > {number_0} AND {kpi_value} < {number_1};",
            'template39': f"SELECT county, {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\' AND {kpi_value} {symbol} {number_0};",
            'template40': f"SELECT * FROM (SELECT t1.state, 100*(t1.kpi - t2.kpi)/t2.kpi AS difference FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference DESC;",
            'template41': f"SELECT * FROM (SELECT t1.state, 100*(t1.kpi - t2.kpi)/t2.kpi AS difference FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference DESC;",
            'template42': f"SELECT * FROM (SELECT t1.county, 100*(t1.kpi - t2.kpi)/t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county) AS t3 WHERE difference > {number_0} AND difference < {number_1} ORDER BY difference DESC;",
            'template43': f"SELECT * FROM (SELECT t1.county, 100*(t1.kpi - t2.kpi)/t2.kpi AS difference FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county) AS t3 WHERE difference {symbol} {number_0} ORDER BY difference DESC;",
       }

         # incase there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if increase:
            if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
                if ge or le:
                    if '%' in CARDINAL[0]:
                        selected_template.append(templates['template42'])
                    else:
                        selected_template.append(templates['template36'])
                elif bet:
                    if '%' in CARDINAL[0]:
                        selected_template.append(templates['template43'])
                    else:
                        selected_template.append(templates['template37'])
            elif place[0] in STATE_LIST:
                if kpi in ("Locations", "Charging_stations", "Charging_points"):
                    selected_template.append(templates['template21'])
                elif kpi == "Charging_points_per_1000_cars":
                    selected_template.append(templates['template25'])
                elif kpi == "Percentage_of_target":
                    selected_template.append(templates['template26'])
                elif kpi == "Cars_per_charging_point":
                    selected_template.append(templates['template27'])
            elif "state" in place[0].lower():
                if kpi in ("Locations", "Charging_stations", "Charging_points"):    
                    if ge or le:
                        if '%' in CARDINAL[0]:
                            selected_template.append(templates['template40'])
                        else:
                            selected_template.append(templates['template23'])
                    elif bet:
                        if '%' in CARDINAL[0]:
                            selected_template.append(templates['template41'])
                        else:
                            selected_template.append(templates['template28'])
                elif kpi == "":
                    if ge or le:
                        selected_template.append(templates['template33'])
                    elif bet:
                        selected_template.append(templates['template29'])
                elif kpi == "Percentage_of_target":
                    if ge or le:
                        selected_template.append(templates['template34'])
                    elif bet:
                        selected_template.append(templates['template30'])
                elif kpi == "Cars_per_charging_point":
                    if ge or le:
                        selected_template.append(templates['template35'])
                    elif bet:
                        selected_template.append(templates['template31'])
            elif "count" in place[0].lower():
                if ge or le:
                    selected_template.append(templates['template24'])
                elif bet:
                    selected_template.append(templates['template32'])
            else:
                # specific county
                selected_template.append(templates['template22'])
        else:
            # absolute
            if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
                if ge or le:
                    selected_template.append(templates['template39'])
                elif bet:
                    selected_template.append(templates['template38'])                        
            elif "state" in place[0].lower():
                if kpi in ("Locations", "Charging_stations", "Charging_points"):
                    if ge == "above average" or ge == "over average" or ge == "more than average":
                        selected_template.append(templates['template5'])
                    elif le == "below average" or le == "under average":
                        selected_template.append(templates['template6'])
                    elif bet:
                        selected_template.append(templates['template7'])
                    elif le or ge:                
                        selected_template.append(templates['template8'])
                elif kpi == "Cars_per_charging_point":
                    if ge == "above average" or ge == "over average" or ge == "more than average":
                        selected_template.append(templates['template11'])
                    elif le == "below average" or le == "under average":
                        selected_template.append(templates['template12'])
                    elif bet:
                        selected_template.append(templates['template16'])
                    elif le or ge:                
                        selected_template.append(templates['template15'])
                elif kpi == "Charging_points_per_1000_cars":
                    if ge == "above average" or ge == "over average" or ge == "more than average":
                        selected_template.append(templates['template13'])
                    elif le == "below average" or le == "under average":
                        selected_template.append(templates['template14'])
                    elif bet:
                        selected_template.append(templates['template18'])
                    elif le or ge:                
                        selected_template.append(templates['template17'])
                elif kpi == "Percentage_of_target":
                    if ge == "above average" or ge == "over average" or ge == "more than average":
                        selected_template.append(templates['template9'])
                    elif le == "below average" or le == "under average":
                        selected_template.append(templates['template10'])
                    elif bet:
                        selected_template.append(templates['template20'])
                    elif le or ge:                
                        selected_template.append(templates['template19'])                                

            else:
                if ge == "above average" or ge == "over average" or ge == "more than average":
                    selected_template.append(templates['template1'])
                elif le == "below average" or le == "under average":
                    selected_template.append(templates['template2'])
                elif bet:
                    selected_template.append(templates['template3'])
                elif le or ge:
                    selected_template.append(templates['template4'])
        
        return selected_template

    def limit_query(self, kpi, place, time, CARDINAL, top, bottom, increase=None, max=None, min=None):
        # place
        if len(place) == 1:
            place_1 = None
        if len(place) == 2:
            place_1 = place[1]
        # time mapping
        mapped_time_start, mapped_time_end = None, None
        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False), self.time_mapping(time_end, False)
        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)
        CARDINAL = CARDINAL[0]

        templates = {
            'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};",
            'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum Limit {CARDINAL};",
            'template3': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} IS NOT NULL ORDER BY {kpi_value} DESC Limit {CARDINAL};",
            'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} IS NOT NULL ORDER BY {kpi_value} Limit {CARDINAL};",
            'template5': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY traffic_chargepoint DESC Limit {CARDINAL};",
            'template6': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY traffic_chargepoint Limit {CARDINAL};",
            'template7': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY chargepoints_per_1000cars DESC Limit {CARDINAL};",
            'template8': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY chargepoints_per_1000cars Limit {CARDINAL};",
            'template9': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY p_o_t DESC Limit {CARDINAL};",
            'template10': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY p_o_t Limit {CARDINAL};",

            'template11': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
            'template12': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

            'template13': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
            'template14': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

            'template15': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
            'template16': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",
           
            'template17': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
            'template18': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

            'template19': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference DESC LIMIT {CARDINAL};",
            'template20': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference ASC LIMIT {CARDINAL};",

            'template21': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference DESC LIMIT {CARDINAL};",
            'template22': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place[0]}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference ASC LIMIT {CARDINAL};",

            'template23': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\' ORDER BY {kpi_value} DESC Limit {CARDINAL};",
            'template24': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\' ORDER BY {kpi_value} ASC Limit {CARDINAL};",

        }

        # incase there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if increase:
            if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
                    if top and max:
                        selected_template.append(templates['template21'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template22'])
                    else:
                        selected_template.append(templates['template21']) 
            elif "state" in place[0].lower():
                if kpi in ("Locations", "Charging_stations", "Charging_points"):
                    if top and max:
                        selected_template.append(templates['template17'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template18'])
                    else:
                        selected_template.append(templates['template17'])
                elif kpi == "Cars_per_charging_point":
                    if top and max:
                        selected_template.append(templates['template15'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template16'])
                    else:
                        selected_template.append(templates['template15'])  
                elif kpi == "Charging_points_per_1000_cars":
                    if top and max:
                        selected_template.append(templates['template11'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template12'])
                    else:
                        selected_template.append(templates['template11'])
                elif kpi == "Percentage_of_target":
                    if top and max:
                        selected_template.append(templates['template13'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template14'])
                    else:
                        selected_template.append(templates['template13'])
               
            else:
                if top and max:
                    selected_template.append(templates['template19'])
                elif (bottom and max) or (top and min) or bottom or min:
                    selected_template.append(templates['template20'])
                else:
                    selected_template.append(templates['template19'])
        else:
            if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
                if top and max:
                    selected_template.append(templates['template23'])
                elif (bottom and max) or (top and min) or bottom or min:
                    selected_template.append(templates['template24'])
                else:
                    selected_template.append(templates['template23']) 
            # check if it is top or below
            elif "state" in place[0].lower():
                if kpi in ("Locations", "Charging_stations", "Charging_points"):
                    if top and max:
                        selected_template.append(templates['template1'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template2'])
                    else:
                        selected_template.append(templates['template1'])
                elif kpi == "Cars_per_charging_point":
                    if top and max:
                        selected_template.append(templates['template5'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template6'])
                    else:
                        selected_template.append(templates['template5'])   
                elif kpi == "Charging_points_per_1000_cars":
                    if top and max:
                        selected_template.append(templates['template7'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template8'])
                    else:
                        selected_template.append(templates['template7'])
                elif kpi == "Percentage_of_target":
                    if top and max:
                        selected_template.append(templates['template9'])
                    elif (bottom and max) or (top and min) or bottom or min:
                        selected_template.append(templates['template10'])
                    else:
                        selected_template.append(templates['template9'])                                          
            else:
                if top and max:
                    selected_template.append(templates['template3'])
                elif (bottom and max) or (top and min) or bottom or min:
                    selected_template.append(templates['template4'])
                else:
                    selected_template.append(templates['template3'])
        
        return selected_template

