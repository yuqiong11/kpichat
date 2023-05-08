import sys
from regex import E
# from sklearn.feature_selection import SelectFromModel

# from torch import q_per_channel_axis, q_per_channel_zero_points
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)
from mappings.kpi_mapping import KPI_MAPPING
from mappings.charger_type_mapping import CHARGER_TYPE_MAPPING
from mappings.time_mapping import CheckTime
from utils.constants import STATE_LIST

class QueryTranslator(CheckTime):
    def __init__(self):
        super().__init__()

    def kpi_mapping(self,kpi):
        return KPI_MAPPING[kpi]

    def charger_type_mapping(self, charger_type):
            return CHARGER_TYPE_MAPPING[charger_type]
    
    def agg_query(self,kpi, place, time, max=None, min=None, avg=None, geo_level=None, increase=None, charger_type = None, operator=None, q_type=None):
        print("q_type", q_type)
        # time mapping
        mapped_time_start, mapped_time_end = None, None

        if not charger_type:
            monthly_form = True
        else:
            monthly_form = False

        if not geo_level:
            if place[0] in STATE_LIST:
                geo_level = 'state'
            else:
                geo_level = 'county'

        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True, monthly_form)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False, monthly_form)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False, True), self.time_mapping(time_end, False, monthly_form) 

        # check if it is a prediction or not
        latest_timestamp = CheckTime.get_latest_timestamp()
        if not mapped_time_end:
            if mapped_time_start > latest_timestamp:
                is_prediction = True
            else: 
                is_prediction = False
        else:
            if mapped_time_end > latest_timestamp:
                is_prediction = True
            else:
                is_prediction = False

        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)

        # charger type mapping
        if charger_type:
            charger_type = self.charger_type_mapping(charger_type)

        templates = {
            # chargepoints, germany
            'template1': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",

            # chargepoints/chargepoints per pkw/percentage, county
            'template2': f"SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place[0]}%\';",
            # avg, chargepoints/chargepoints per pkw/percentage, county 
            'template3': f"SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",
            # max, chargepoints/chargepoints per pkw/percentage, county
            'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MAX({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AND month={mapped_time_start};",
            # min, chargepoints/chargepoints per pkw/percentage, county
            'template5': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE {kpi_value} = (SELECT MIN({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AND month={mapped_time_start};",
        
            # chargepoints, state
            'template6': f"SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\';",
            # avg, chargepoints, state
            'template7': f"SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",
            # max, chargepoints, state
            'template8': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC LIMIT 1;", 
            # min, chargepoints, state
            'template9': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum ASC LIMIT 1;",

            # chargepoints per pkw, germany
            'template53': f"SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start};",

            # chargepoints per pkw, state
            'template10': f"SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\';",
            # max, chargepoints per pkw, state
            'template11': f"SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) as charge_pkw, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY charge_pkw DESC LIMIT 1;",
            # min, chargepoints per pkw, state
            'template12': f"SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) as charge_pkw, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY charge_pkw ASC LIMIT 1;",
            # avg, chargepoints per pkw, state
            'template13': f"SELECT AVG(t.charge_pkw) FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS charge_pkw FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t",

            # percentage, germany
            'template54': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start};",

            # percentage, state
            'template14': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} AND state=\'{place[0]}\';",
            # max, percentage, state
            'template15': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state ORDER BY p_o_t DESC LIMIT 1;",
            # min, percentage, state
            'template16': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state ORDER BY p_o_t ASC LIMIT 1;",
            # avg, percentage, state
            'template17': f"SELECT AVG(p_o_t) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month = {mapped_time_start} GROUP BY state) t;",
           
            # increase, chargepoints, germany
            'template18': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",
            # increase, chargepoints per pkw, germany
            'template55': f"SELECT (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",
            # increase, percentage, germany
            'template56': f"SELECT (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",

            # increase, chargepoints, state
            'template52': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state = \'{place[0]}\') - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            # increase, max, chargepoints, state
            'template19': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",
            # increase, min, chargepoints, state
            'template20': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",
            # increase, avg, chargepoints, state
            'template21': f"SELECT (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) - (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",

            # increase, chargepoints per pkw, state
            'template22': f"SELECT (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state = \'{place[0]}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state = \'{place[0]}\') AS difference;",
            # increase, max, chargepoints per pkw, state
            'template23': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",
            # increase, min, chargepoints per pkw, state
            'template24': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",        
            # increase, avg, chargepoints per pkw, state
            'template25': f"SELECT AVG(t1.kpi-t2.kpi) FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state;",
            
            # increase, percentage, state
            'template26': f"SELECT (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place[0]}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') AS difference;",
            # increase, max, percentage, state
            'template27': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT 1;",            
            # increase, min, percentage, state
            'template28': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT 1;",     
            # increase, avg, percentage, state
            'template29': f"SELECT AVG(t1.kpi-t2.kpi) FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state;",

            # increase, chargepoints/chargepoints per pkw/percentage, county
            'template30': f"SELECT (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND county LIKE \'%{place[0]}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place[0]}%\');",
            # increase, max, chargepoints/chargepoints per pkw/percentage, county
            'template31': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference DESC LIMIT 1;",
            # increase, min, chargepoints/chargepoints per pkw/percentage, county
            'template32': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference ASC LIMIT 1;",       
            # increase, avg, chargepoints/chargepoints per pkw/percentage, county
            'template33': f"SELECT (SELECT SUM({kpi_value})/COUNT(county) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) - (SELECT SUM({kpi_value})/COUNT(county) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) AS difference;",

            # fast/normal, chargepoints, germany
            'template34': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\';",
            # fast/normal, chargepoints, state
            'template35': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[0]}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\';",
            # fast/normal, max, chargepoints, state
            'template36': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), bundesland FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY bundesland ORDER BY sum DESC LIMIT 1;",
            # fast/normal, min, chargepoints, state
            'template37': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), bundesland FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY bundesland ORDER BY sum ASC LIMIT 1;",
            # fast/normal, avg, chargepoints, state
            'template38': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER))/COUNT(DISTINCT(bundesland)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\';",
            # fast/normal, chargepoints, county
            'template39': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND landkreis LIKE \'%{place[0]}%\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\';",
            # fast/normal, max, chargepoints, county
            'template40': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY landkreis ORDER BY sum DESC LIMIT 1;",
            # fast/normal, min, chargepoints, county
            'template41': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY landkreis ORDER BY sum ASC LIMIT 1;",
            # fast/normal, avg, chargepoints, county
            'template42': f"SELECT AVG(t.kpi) FROM (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) AS kpi FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY landkreis) t",

            # increase, fast/normal, chargepoints, germany
            'template43': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\';",
            # increase, fast/normal, chargepoints, state
            'template44': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[0]}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\';",
            # increase, fast/normal, max, chargepoints, state
            'template45': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), bundesland FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY bundesland ORDER BY sum DESC LIMIT 1;",
            # increase, fast/normal, min, chargepoints, state
            'template46': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), bundesland FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY bundesland ORDER BY sum ASC LIMIT 1;",
            # increase, fast/normal, avg, chargepoints, state
            'template47': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER))/COUNT(DISTINCT(bundesland)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\';",
            # increase, fast/normal, chargepoints, county
            'template48': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND landkreis LIKE \'%{place[0]}%\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\';",
            # increase, fast/normal, max, chargepoints, county
            'template49': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY landkreis ORDER BY sum DESC LIMIT 1;",
            # increaes, fast/normal, min, chargepoints, county
            'template50': f"SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND landkreis LIKE \'%{place[0]}%\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY landkreis ORDER BY sum ASC LIMIT 1;",
            # increase, fast/normal, avg, chargepoints, county
            'template51': f"SELECT AVG(t.kpi) FROM (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) AS kpi FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY landkreis) t",
        }
        # incase there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if not charger_type:
            # query not including charger_type
            if increase:
                print('increased')
                # template 18-33, 52, 55, 56
                # queries about increase
                if geo_level == "germany":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template55'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template56'])
                    else:
                        selected_template.append(templates['template18'])

                elif geo_level == "state":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template22'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template26'])
                    else:
                        selected_template.append(templates['template52'])
                
                elif geo_level == "county":
                    selected_template.append(templates['template30'])
               

                elif max and geo_level == "state":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template23'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template27'])
                    else:
                        selected_template.append(templates['template19'])

                elif min and geo_level == "state":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template24'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template28'])
                    else:
                        selected_template.append(templates['template20'])

                elif avg and geo_level == "state":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template25'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template29'])
                    else:
                        selected_template.append(templates['template21'])

                elif max and geo_level == "county":
                    selected_template.append(templates['template31'])

                elif min and geo_level == "county":
                    selected_template.append(templates['template32'])

                elif avg and geo_level == "county":
                    selected_template.append(templates['template33'])   

            else:
                # template 1-17, 53, 54
                # queries not about increase
                if geo_level == "county":
                    if avg:
                        selected_template.append(templates['template3'])
                    elif max:
                        selected_template.append(templates['template4'])
                    elif min:
                        selected_template.append(templates['template5'])
                    else:
                        selected_template.append(templates['template2'])

                elif geo_level == "germany":
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template53'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template54'])
                    else:
                        selected_template.append(templates['template1'])

                elif geo_level == "state":
                    if kpi == "Chargepoints per 1000 cars":
                        if max:
                            selected_template.append(templates['template11'])
                        elif min:
                            selected_template.append(templates['template12'])
                        elif avg:
                            selected_template.append(templates['template13'])
                        else:
                            selected_template.append(templates['template10'])
                    elif kpi == "Percentage of target":
                        if max:
                            selected_template.append(templates['template15'])
                        elif min:
                            selected_template.append(templates['template16'])
                        elif avg:
                            selected_template.append(templates['template17'])
                        else:                        
                            selected_template.append(templates['template14'])
                    else:
                        if max:
                            selected_template.append(templates['template8'])
                        elif min:
                            selected_template.append(templates['template9'])
                        elif avg:
                            selected_template.append(templates['template7'])
                        else:    
                            selected_template.append(templates['template6'])     
        else:
            # query including charger_type
            # template 34-51                           
            if increase:
                print('increased')
                # template 43-51
                # queries about increase
                if geo_level == "germany":
                    selected_template.append(templates['template43'])

                elif geo_level == "state":
                    if max:
                        selected_template.append(templates['template45'])
                    elif min:
                        selected_template.append(templates['template46'])
                    elif avg: 
                        selected_template.append(templates['template47'])
                    else:
                        selected_template.append(templates['template44'])
                
                elif geo_level == "county":
                    if max:
                        selected_template.append(templates['template49'])
                    elif min:
                        selected_template.append(templates['template50'])
                    elif avg: 
                        selected_template.append(templates['template51'])
                    else:
                        selected_template.append(templates['template48'])

            else:
                # template 34-42
                # queries not about increase
                if geo_level == "germany":
                    selected_template.append(templates['template34'])

                elif geo_level == "state":
                    if max:
                        selected_template.append(templates['template36'])
                    elif min:
                        selected_template.append(templates['template37'])
                    elif avg: 
                        selected_template.append(templates['template38'])
                    else:
                        selected_template.append(templates['template35'])
                
                elif geo_level == "county":
                    if max:
                        selected_template.append(templates['template40'])
                    elif min:
                        selected_template.append(templates['template41'])
                    elif avg: 
                        selected_template.append(templates['template42'])
                    else:
                        selected_template.append(templates['template39'])
        print(selected_template)

        return is_prediction, selected_template[0]

    def compare_query(self,kpi, place, time, increase=None, charger_type = None, q_type=None):
        print("increase", increase)
        # place
        place_1, place_2 = place[0], place[1]

        # check if place is county or state level
        if (place_1 in STATE_LIST) or (place_2 in STATE_LIST):
            geo_level = 'state'
        else:
            geo_level = 'county'

        # time mapping
        mapped_time_start, mapped_time_end = None, None

        if not charger_type:
            monthly_form = True
        else:
            monthly_form = False

        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True, monthly_form)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False, monthly_form)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False, True), self.time_mapping(time_end, False, monthly_form) 

        # check if it is a prediction or not
        latest_timestamp = CheckTime.get_latest_timestamp()
        if not mapped_time_end:
            if mapped_time_start > latest_timestamp:
                is_prediction = True
            else: 
                is_prediction = False
        else:
            if mapped_time_end > latest_timestamp:
                is_prediction = True
            else:
                is_prediction = False

        # kpi mapping
        kpi_value = self.kpi_mapping(kpi)

        # charger type mapping
        if charger_type:
            charger_type = self.charger_type_mapping(charger_type)

        templates = {
            # chargepoints, state 
            'template1': f"SELECT (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\') - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\')",
            # chargepoint_pkw, state
            'template2': f"SELECT (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\') ",
            # percentage, state
            'template3': f"SELECT (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\') ",
            # chargepoints/chargepoint_pkw/percentage, county
            'template4': f"SELECT (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place_1}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place_2}%\')",
            # fast/normal chargepoints, state
            'template5': f"SELECT ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland=\'{place_1}\') - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland=\'%{place_2}%\')) ",
            # fast/normal chargepoints, county
            'template6': f"SELECT ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\') - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_2}%\')) ",
    
            # increase, chargepoints, state 
            'template7': f"SELECT ((SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_1}\') - (SELECT SUM(no_total_chargepoints) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\'))  -  ((SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_2}\') - (SELECT SUM({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\'))",
            # increase, chargepoint_pkw, state
            'template8': f"SELECT ((SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_1}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\'))  -  ((SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_2}\') - (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\'))",
            # increase, percentage, state
            'template9': f"SELECT ((SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_1}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_1}\'))  -  ((SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place_2}\') - (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place_2}\'))",
            # increase, chargepoints/chargepoint_pkw/percentage, county
            'template10': f"SELECT ((SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND county LIKE \'%{place_1}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place_1}%\')) - ((SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND county LIKE \'%{place_2}%\') - (SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND county LIKE \'%{place_2}%\'))",
            # increase, fast/normal chargepoints, state
            'template11': f"SELECT (ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\') AND bundesland=\'{place_1}\' - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland=\'{place_1}\')) -  (ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\') AND bundesland=\'{place_2}\' - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland=\'{place_2}\'))",
            # increase, fast/normal chargepoints, county
            'template12': f"SELECT (ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\') AND landkreis LIKE \'%{place_1}%\') - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\') AND landkreis LIKE \'%{place_1}%\')) - (ROUND ((SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\') AND landkreis LIKE \'%{place_2}%\') - (SELECT SUM(CAST(anzahl_ladepunkte AS INTEGER)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\') AND landkreis LIKE \'%{place_2}%\'))",
        }

        selected_template = []

        if increase:
            # queries about increase
            if charger_type and kpi:
                if geo_level == 'state':
                    selected_template.append(templates['template11'])
                else:
                    selected_template.append(templates['template12'])
            else:
                if geo_level == 'state':
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template8'])
                    elif kpi == "Percentage of target":
                        selected_template.append(templates['template9'])
                    else:
                        selected_template.append(templates['template7'])
                else:
                    selected_template.append(templates['template10'])

        else:
            # queries not about increase
            if charger_type and kpi:
                if geo_level == 'state':
                    selected_template.append(templates['template5'])
                else:
                    selected_template.append(templates['template6'])
            else:
                if geo_level == 'state':
                    if kpi == "Chargepoints per 1000 cars":
                        selected_template.append(templates['template2'])
                    elif kpi == "Percentage of target":
                        print("checkpoint")
                        print(mapped_time_start)
                        selected_template.append(templates['template3'])
                    else:
                        selected_template.append(templates['template1'])
                else:
                    selected_template.append(templates['template4'])

        return is_prediction, selected_template[0]

    def charger_operator_query(self, kpi, place, time, max=None, min=None, geo_level=None, increase=None,charger_type=None, operator=None,q_type=None):
        # questions
        # measures how many charging points do each operator have in total
        # what kind of operators are there in berlin/sachsen/Germany 
        # strongest/weakest operators in berlin/sachsen/Germany

        # time mapping
        mapped_time_start, mapped_time_end = None, None

        monthly_form = False

        # place
        if not place:
            place_1 = None
        else: 
            place_1 = place[0]

        if increase and len(time) == 1:
            # do the time mapping first
            mapped_time_start, mapped_time_end = self.time_mapping(time[0], True, monthly_form)
        elif len(time) == 1:
            # not asking for increase
            mapped_time_start = self.time_mapping(time[0], False, monthly_form)
        else:
            # time list has 2 elements
            # workaround way of checking whether time is only year, e.g. 2020(length 4)
            # from 2019 to 2021 = from 12.2018 to 12.2021
            time_start, time_end = time[0], time[1]
            if len(time_start) == 4:
                time_start = "12."+str(int(time_start)-1)
            if len(time_end) == 4:
                time_end = "12."+time_end
            mapped_time_start, mapped_time_end = self.time_mapping(time_start, False, monthly_form), self.time_mapping(time_end, False, monthly_form) 

        is_prediction = False

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
        '''
        templates = {
            # operator, germany
            'template1': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source  WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number DESC;",
            # operator, max, germany
            'template4': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            # operator, min, germany
            'template7': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

            # operator, state
            'template3': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number DESC;",
            # operator, max, state
            'template6': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",        
            # operator, min, state
            'template9': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

            # operator, county
            'template2': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number DESC;",
            # operator, max, county
            'template5': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            # operator, min, county
            'template8': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

            # increase, operator, germany
            'template10': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source  WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number DESC;",
            # increase, operator, max, germany
            'templat11': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            # increase, operator, min, germany
            'template12': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

            # increase, operator, state
            'template13': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' AND bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number DESC;",
            # increase, operator, max, state
            'template14': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' AND bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",        
            # increase, operator, min, state
            'templat15': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' bundesland = \'{place_1}\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

            # increase, operator, county
            'template16': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number DESC;",
            # increase, operator, max, county
            'template17': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number DESC LIMIT 1;",
            # increase, operator, min, county
            'template18': f"SELECT betreiber, SUM(CAST(anzahl_ladepunkte AS INT)) AS number FROM \"E-Mobility\".emo_bna_source WHERE to_date(inbetriebnahmedatum,'DD-MM-YYYY') <= \'{mapped_time_end}\' AND to_date(inbetriebnahmedatum,'DD-MM-YYYY') >= \'{mapped_time_start}\' AND landkreis LIKE \'%{place_1}%\' GROUP BY betreiber ORDER BY number ASC LIMIT 1;",

        }
        # in case there are more than 1 template returned
        # e.g. if percentage of a kpi needs to be shown in the response
        selected_template = []

        if increase:
            # template 10-18
            if geo_level == "germany":
                if max: 
                    selected_template.append(templates['templat11'])
                elif min: 
                    selected_template.append(templates['template12'])
                else:
                    selected_template.append(templates['template10'])
            elif geo_level == "state":
                if max: 
                    selected_template.append(templates['template14'])
                elif min: 
                    selected_template.append(templates['template15'])
                else:
                    selected_template.append(templates['template13'])
            else:
                if max: 
                    selected_template.append(templates['template17'])
                elif min: 
                    selected_template.append(templates['template18'])
                else:
                    selected_template.append(templates['template16'])
        else:
            # template 1-9
            if geo_level == "germany":
                if max: 
                    selected_template.append(templates['template4'])
                elif min: 
                    selected_template.append(templates['template7'])
                else:
                    selected_template.append(templates['template1'])
            elif geo_level == "state":
                if max: 
                    selected_template.append(templates['template6'])
                elif min: 
                    selected_template.append(templates['template9'])
                else:
                    selected_template.append(templates['template3'])
            else:
                if max: 
                    selected_template.append(templates['template5'])
                elif min: 
                    selected_template.append(templates['template8'])
                else:
                    selected_template.append(templates['template2'])

        return is_prediction, selected_template[0]
















    # def limit_query(self, kpi, place, time, CARDINAL, top, bottom, increase=None, max=None, min=None):
    #     # place
    #     if len(place) == 1:
    #         place_1 = None
    #     if len(place) == 2:
    #         place_1 = place[1]
    #     # time mapping
    #     mapped_time_start, mapped_time_end = None, None
    #     if increase and len(time) == 1:
    #         # do the time mapping first
    #         mapped_time_start, mapped_time_end = self.time_mapping(time[0], True)
    #     elif len(time) == 1:
    #         # not asking for increase
    #         mapped_time_start = self.time_mapping(time[0], False)
    #     else:
    #         # time list has 2 elements
    #         # workaround way of checking whether time is only year, e.g. 2020(length 4)
    #         # from 2019 to 2021 = from 12.2018 to 12.2021
    #         time_start, time_end = time[0], time[1]
    #         if len(time_start) == 4:
    #             time_start = "12."+str(int(time_start)-1)
    #         if len(time_end) == 4:
    #             time_end = "12."+time_end
    #         mapped_time_start, mapped_time_end = self.time_mapping(time_start, False), self.time_mapping(time_end, False)
    #     # kpi mapping
    #     kpi_value = self.kpi_mapping(kpi)
    #     CARDINAL = CARDINAL[0]

    #     templates = {
    #         'template1': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};",
    #         'template2': f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY sum Limit {CARDINAL};",
    #         'template3': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} IS NOT NULL ORDER BY {kpi_value} DESC Limit {CARDINAL};",
    #         'template4': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND {kpi_value} IS NOT NULL ORDER BY {kpi_value} Limit {CARDINAL};",
    #         'template5': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY traffic_chargepoint DESC Limit {CARDINAL};",
    #         'template6': f"SELECT SUM(traffic)/SUM(no_total_chargepoints) AS traffic_chargepoint, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY traffic_chargepoint Limit {CARDINAL};",
    #         'template7': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY chargepoints_per_1000cars DESC Limit {CARDINAL};",
    #         'template8': f"SELECT SUM(no_total_chargepoints)/(SUM(traffic)/1000) AS chargepoints_per_1000cars, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY chargepoints_per_1000cars Limit {CARDINAL};",
    #         'template9': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY p_o_t DESC Limit {CARDINAL};",
    #         'template10': f"SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS p_o_t, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state ORDER BY p_o_t Limit {CARDINAL};",

    #         'template11': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template12': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end if mapped_time_end else ''} GROUP BY state) t1 left join (SELECT 1000*SUM(no_total_chargepoints)/SUM(traffic) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

    #         'template13': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template14': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT 100*SUM(no_total_chargepoints)/SUM(normalized_chargepoint_target) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

    #         'template15': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template16': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM(traffic)/SUM(no_total_chargepoints) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",
           
    #         'template17': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template18': f"SELECT t1.kpi - t2.kpi AS difference, t1.state FROM (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} GROUP BY state) t1 left join (SELECT SUM({kpi_value}) AS kpi, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} GROUP BY state) t2 on t1.state = t2.state ORDER BY difference ASC LIMIT {CARDINAL};",

    #         'template19': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template20': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end}) t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start}) t2 on t1.county = t2.county ORDER BY difference ASC LIMIT {CARDINAL};",

    #         'template21': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference DESC LIMIT {CARDINAL};",
    #         'template22': f"SELECT t1.kpi - t2.kpi AS difference, t1.county FROM (SELECT {kpi_value} AS kpi, county, state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_end} AND state=\'{place}\') t1 left join (SELECT {kpi_value} AS kpi, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[0]}\') t2 on t1.county = t2.county ORDER BY difference ASC LIMIT {CARDINAL};",

    #         'template23': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[1]}\' ORDER BY {kpi_value} DESC Limit {CARDINAL};",
    #         'template24': f"SELECT {kpi_value}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time_start} AND state=\'{place[1]}\' ORDER BY {kpi_value} ASC Limit {CARDINAL};",

    #     }

    #     # incase there are more than 1 template returned
    #     # e.g. if percentage of a kpi needs to be shown in the response
    #     selected_template = []

    #     if increase:
    #         if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
    #                 if top and max:
    #                     selected_template.append(templates['template21'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template22'])
    #                 else:
    #                     selected_template.append(templates['template21']) 
    #         elif "state" in place[0].lower():
    #             if kpi in ("Locations", "Charging_stations", "Charging_points"):
    #                 if top and max:
    #                     selected_template.append(templates['template17'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template18'])
    #                 else:
    #                     selected_template.append(templates['template17'])
    #             elif kpi == "Cars_per_charging_point":
    #                 if top and max:
    #                     selected_template.append(templates['template15'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template16'])
    #                 else:
    #                     selected_template.append(templates['template15'])  
    #             elif kpi == "Chargepoints per 1000 cars":
    #                 if top and max:
    #                     selected_template.append(templates['template11'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template12'])
    #                 else:
    #                     selected_template.append(templates['template11'])
    #             elif kpi == "Percentage of target":
    #                 if top and max:
    #                     selected_template.append(templates['template13'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template14'])
    #                 else:
    #                     selected_template.append(templates['template13'])
               
    #         else:
    #             if top and max:
    #                 selected_template.append(templates['template19'])
    #             elif (bottom and max) or (top and min) or bottom or min:
    #                 selected_template.append(templates['template20'])
    #             else:
    #                 selected_template.append(templates['template19'])
    #     else:
    #         if len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
    #             if top and max:
    #                 selected_template.append(templates['template23'])
    #             elif (bottom and max) or (top and min) or bottom or min:
    #                 selected_template.append(templates['template24'])
    #             else:
    #                 selected_template.append(templates['template23']) 
    #         # check if it is top or below
    #         elif "state" in place[0].lower():
    #             if kpi in ("Locations", "Charging_stations", "Charging_points"):
    #                 if top and max:
    #                     selected_template.append(templates['template1'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template2'])
    #                 else:
    #                     selected_template.append(templates['template1'])
    #             elif kpi == "Cars_per_charging_point":
    #                 if top and max:
    #                     selected_template.append(templates['template5'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template6'])
    #                 else:
    #                     selected_template.append(templates['template5'])   
    #             elif kpi == "Chargepoints per 1000 cars":
    #                 print('check')
    #                 if top and max:
    #                     selected_template.append(templates['template7'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template8'])
    #                 else:
    #                     selected_template.append(templates['template7'])
    #             elif kpi == "Percentage of target":
    #                 if top and max:
    #                     selected_template.append(templates['template9'])
    #                 elif (bottom and max) or (top and min) or bottom or min:
    #                     selected_template.append(templates['template10'])
    #                 else:
    #                     selected_template.append(templates['template9'])                                          
    #         else:
    #             if top and max:
    #                 selected_template.append(templates['template3'])
    #             elif (bottom and max) or (top and min) or bottom or min:
    #                 selected_template.append(templates['template4'])
    #             else:
    #                 selected_template.append(templates['template3'])
        
    #     return selected_template







    # def charger_type_query(self, place, charger_type, max=None, min=None, avg=None):
    #     # questions 
    #     # fast/normal chargers in berlin/sachsen/Germany
    #     # max/min fast/normal chargers in berlin/sachsen
    #     # avg of fast/normal chargers of a county of sachsen/ a county/ a state

    #     # place
    #     if len(place) == 1:
    #         place_1 = None
    #     if len(place) == 2:
    #         place_1 = place[1]
    #     # charger type mapping
    #     charger_type = self.charger_type_mapping(charger_type)

    #     '''
    #         'template1': f"fast/normal in germany",
    #         'template2': f"fast/normal in berlin",
    #         'template3': f"fast/normal in sachsen",
    #         'template4': f"county with max of fast/normal",
    #         'template5': f"county with min of fast/normal",
    #         'template6': f"state with max of fast/normal",
    #         'template7': f"state with min of fast/normal",
    #         'template8': f"avg of fast/normal of a county",
    #         'template9': f"avg of fast/normal of a state",
    #         'template10': f"avg of fast/normal of a county in sachsen"
    #         'template11': f"county in a state with max of fast/normal"
    #         'template12':f"county in a state with min of fast/normal"
    #     '''
    #     templates = {
    #         'template1': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\';",
    #         'template2': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND landkreis LIKE \'%{place[0]}%\';",
    #         'template3': f"SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[0]}\';",
    #         'template4': f"SELECT landkreis, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' GROUP BY landkreis ORDER BY count DESC LIMIT 1;",
    #         'template5': f"SELECT landkreis, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' GROUP BY landkreis ORDER BY count ASC LIMIT 1;",
    #         'template6': f"SELECT bundesland, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' GROUP BY bundesland ORDER BY count DESC LIMIT 1;",
    #         'template7': f"SELECT bundesland, COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' GROUP BY bundesland ORDER BY count ASC LIMIT 1;",
    #         'template8': f"SELECT COUNT(*)/COUNT(DISTINCT(landkreis)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\';",
    #         'template9': f"SELECT COUNT(*)/COUNT(DISTINCT(bundesland)) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\';",
    #         'template10': f"SELECT AVG(count) FROM (SELECT COUNT(*) FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[0]}\' GROUP BY landkreis) AS t;",
    #         'template11': f"SELECT COUNT(*), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[1]}\' GROUP BY landkreis ORDER BY count DESC LIMIT 1;",
    #         'template12': f"SELECT COUNT(*), landkreis FROM \"E-Mobility\".emo_bna_source WHERE art_der_ladeeinrichtung=\'{charger_type}\' AND bundesland = \'{place[1]}\' GROUP BY landkreis ORDER BY count ASC LIMIT 1;"
    #     }
    #     # in case there are more than 1 template returned
    #     # e.g. if percentage of a kpi needs to be shown in the response
    #     selected_template = []

    #     # template 1-12
    #     if len(place) ==1 and place[0].lower() == "germany":
    #         selected_template.append(templates['template1'])
    #     elif len(place)==1 and place[0] in STATE_LIST:
    #         if max:
    #             # percentage as additional info
    #             selected_template.append(templates['template4'])
    #             selected_template.append(templates['template1'])
    #         elif min:
    #             # percentage as additional info
    #             selected_template.append(templates['template5'])
    #             selected_template.append(templates['template1'])
    #         else:
    #             selected_template.append(templates['template3'])
    #             selected_template.append(templates['template1'])
    #     elif len(place) ==1 and "state" in place[0].lower():
    #         if avg: 
    #             selected_template.append(templates['template9'])
    #         elif max:
    #             selected_template.append(templates['template6'])
    #             selected_template.append(templates['template1'])
    #         elif min:
    #             selected_template.append(templates['template7'])
    #             selected_template.append(templates['template1'])
    #     elif len(place) ==1 and place[0].lower() in ("county", "counties"):
    #         if avg:
    #             selected_template.append(templates['template8'])
    #         elif max:
    #             selected_template.append(templates['template4'])
    #             selected_template.append(templates['template1'])
    #         elif min:
    #             selected_template.append(templates['template5'])
    #             selected_template.append(templates['template1'])
    #     elif len(place) == 2 and ("count" in place[0].lower() or "count" in place[1].lower()):
    #         if avg:
    #             selected_template.append(templates['template10'])
    #         elif max:
    #             selected_template.append(templates['template11'])
    #             selected_template.append(templates['template1'])
    #         elif min:
    #             selected_template.append(templates['template12'])
    #             selected_template.append(templates['template1'])
    #     else:
    #         # percentage as additional info
    #         selected_template.append(templates['template2'])
    #         selected_template.append(templates['template1'])

    #     return selected_template