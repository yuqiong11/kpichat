# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import psycopg2
import datetime

class ActionConvertDate(Action):

    def name(self) -> Text:
        return "action_convert_date"

    def run(self, dispatcher, tracker, domain):
        
        slot_year= ""
        slot_month=""

        DATE = tracker.get_slot("DATE")

        months_of_text = [
        'Jan', 'Feb', 'Mar',
        'Apr', 'May', 'Jun', 
        'Jul', 'Aug', 'Sept',
        'Oct', 'Nov', 'Dec'
        ]
        months_of_number_1 = [
        '01.20', '02.20', '03.20', '04.20', '05.20', '06.20', '07.20', '08.20', '09.20', '10.20', '11.20', '12.20'    
        ]
        months_of_number_2 = [
        '.01', '.02', '.03', '.04', '.05', '.06', '.07', '.08', '.09', '.10', '.11', '.12'   
        ]
        months_of_number_3 = [
        '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'   
        ]
        years = ['2022', '2021', '2020', '2019', '2018', '2017']
        special_words_01 = ['beginning', 'first']
        special_words_02 = ['end', 'twelfth', 'last month of']

        if DATE[:4] in years and DATE[4:6] in months_of_number_3:
            mapped_time = DATE
        elif DATE[:2] in months_of_number_3 and DATE[2:6] in years:
            mapped_time = DATE[2:6] + DATE[:2]
        else:

            #search for year
            for year in years:
                if year in DATE:
                    slot_year = year
                    break

            #search for month
            for word in special_words_01:
                if word in DATE:
                    slot_month='01'
                    break

            if slot_month == "":
                for word in special_words_02:
                    if word in DATE:
                        slot_month='12'

            if slot_month == "":
                if DATE == 'now':
                    current_month = datetime.datetime.now().month
                    slot_year=str(datetime.datetime.now().year)
                    if current_month < 10:
                        slot_month='0'+str(current_month)
                    else:
                        slot_month=current_month

            if slot_month == "":    
                if 'last month' in DATE:
                    current_date = datetime.datetime.now()
                    d = datetime.timedelta(days = 30)
                    required_date = current_date - d
                    slot_year=str(required_date.year)
                    if required_date.month < 10:
                        slot_month='0'+str(required_date.month)
                    else:
                        slot_month=required_date.month

            if slot_month == "":
                if 'next month' in DATE:
                    current_date = datetime.datetime.now()
                    d = datetime.timedelta(days = 30)
                    required_date = current_date + d
                    slot_year=str(required_date.year)
                    if required_date.month < 10:
                        slot_month='0'+str(required_date.month)
                    else:
                        slot_month=required_date.month  

            
            if slot_month == "":
                if 'second month' in DATE:
                    slot_month='02'
                    
            if slot_month == "":
                if 'third month' in DATE:
                    slot_month='03'

            if slot_month == "":
                for i in range(len(months_of_text)):
                    if months_of_text[i] in DATE:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)
            
            if slot_month == "":
                for i in range(len(months_of_number_1)):
                    if months_of_number_1[i] in DATE:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)

            if slot_month == "":
                for i in range(len(months_of_number_2)):
                    if months_of_number_2[i] in DATE:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)

            mapped_time = slot_year+slot_month
                    
        return [SlotSet("mapped_time", mapped_time)]
        


class ActionQueryClarify(Action):

    def name(self) -> Text:
        return "action_query_clarify"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place is {place}")
        dispatcher.utter_message(text=f"time is {mapped_time}")
        dispatcher.utter_message(text=f"kpi is {kpi}")

        return []


class ActionResetSlots(Action):

    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("DATE", None), SlotSet("mapped_time", None)]

class ActionSlotCheck(Action):

    def name(self) -> Text:
        return "action_slot_check"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place: {place}\n kpi: {kpi}\n time:{DATE}")

        return []

class ActionQueryConfirm(Action): 

    def name(self) -> Text:
        return "action_query_confirm"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place: {place}\n kpi: {kpi}\n time:{mapped_time}?",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])
        return []

class ActionExecuteAggQuery(Action):
   def name(self) -> Text:
      return "action_execute_agg_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        avg = tracker.get_slot("avg")
        user_input = tracker.latest_message['text']

        states_list = ('Sachsen','Baden-Württemberg','Bayern', 'Brandenburg', 'Hessen', 'Niedersachsen', 
                        'Mecklenburg-Vorpommern', 'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen-Anhalt',
                        'Schleswig-Holstein', 'Thüringen')
        # first: convert kpi to its column name in database
        if kpi == 'Locations':
            kpi_value = 'no_total_locations'
        elif kpi == 'Charging stations':
            kpi_value = 'no_total_stations'
        elif kpi == 'Charging points':
            kpi_value = 'no_total_chargepoints'

        # second: check if agg function exists
        if max != None and (place != 'federal state' or 'state'):
            kpi_value=f"MAX({kpi_value})"
            if place in states_list:
                state_value=f"state='{place}' AND"
            else:                    
                state_value=""
        elif min != None and (place != 'federal state' or 'state'):
            kpi_value=f"MIN({kpi_value})"
            if place in states_list:
                state_value=f"state='{place}' AND"
            else:                    
                state_value=""               
        elif avg != None and (place != 'federal state' or 'state'):
            kpi_value=f"AVG({kpi_value})"
            if place in states_list:
                state_value=f"state='{place}' AND"
            else:                    
                state_value=""   
        else:
            # third: check different state types
            if place == 'Germany' or (place in 'federal states' or place in 'states'):
                kpi_value=f"SUM({kpi_value})"
                state_value=""
            elif place == 'county':
                state_value=""
            elif avg != None and (place == 'federal state' or 'state'):
                state_value=""
                kpi_value=f"SUM({kpi_value})/COUNT(DISTINCT(state))"            
            elif place in ('Berlin', 'Hamburg'):
                state_value=f"state='{place}' AND"
            elif place in states_list:
                state_value=f"state='{place}' AND"
                kpi_value=f"SUM({kpi_value})"                  
            else:
                state_value=f"county LIKE '%{place}%' AND"
                
        q = f"SELECT {kpi_value} FROM \"E-Mobility\".emo_historical WHERE {state_value} month={mapped_time};"

        cur.execute(q)
        result = cur.fetchall()
        if len(result) == 1:
            dispatcher.utter_message(text=f"The{max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {place} in {DATE} is "+str(round(result[0][0])))

        return []



class ActionExecuteGroupSortQuery(Action):
   def name(self) -> Text:
      return "action_execute_group_sort_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        desc = tracker.get_slot("desc")
        asc = tracker.get_slot("asc")

        # first: convert kpi to its column name in database
        if kpi == 'Locations':
            kpi_value = 'no_total_locations'
        elif kpi == 'Charging stations':
            kpi_value = 'no_total_stations'
        elif kpi == 'Charging points':
            kpi_value = 'no_total_chargepoints'
        
        # second: check if desc or asc exists
        if desc == None and asc == None:
            q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;"
        elif desc != None:
            q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;"
        elif asc != None:
            q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;"

        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result[0]}")

        return []



class ActionExecuteFilterQuery(Action):
   def name(self) -> Text:
      return "action_execute_filter_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        ge = tracker.get_slot("ge")
        le = tracker.get_slot("le")
        bet = tracker.get_slot("bet")
        user_input = tracker.latest_message['text']

        # first: convert kpi to its column name in database
        if kpi == 'Locations':
            kpi_value = 'no_total_locations'
        elif kpi == 'Charging stations':
            kpi_value = 'no_total_stations'
        elif kpi == 'Charging points':
            kpi_value = 'no_total_chargepoints'

        # second: check if comparative symbols exist
        if ge != None:
            symbol = '>='
            number = ge.split()[-1]
        elif le != None:
            symbol = '<='
            number = le.split()[-1]
        elif bet != None:
            number_l = bet.split()[1]
            number_r = bet.split()[-1]
        # check for column name
        if place == 'county' or 'counties':
            column_value = f"county, {kpi_value}"
            if "above average" in user_input:
                filter_clause = f"month={mapped_time} AND {kpi_value} > (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time})"
            elif "below average" or "under average" in user_input:
                filter_clause = f"month={mapped_time} AND {kpi_value} < (SELECT AVG({kpi_value}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time})" 
            elif bet != None:
                filter_clause = f"month={mapped_time} AND {kpi_value} > {number_l} AND {kpi_value} < {number_r}"
            else:
                filter_clause = f"month={mapped_time} AND {kpi_value} {symbol} {number}"
            
        elif place == 'state' or 'states' or 'federal states':
            column_value = f"state, SUM({kpi_value})"
            if "above average" in user_input:
                filter_clause = f"month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time})"
            elif "below average" or "under average" in user_input:
                filter_clause = f"month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) < (SELECT SUM({kpi_value})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time})"
            elif bet != None:
                filter_clause = f"month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) > {number_l} AND SUM({kpi_value}) < {number_r}"
            else:
                filter_clause = f"month={mapped_time} GROUP BY state HAVING SUM({kpi_value}) {symbol} {number}"


        q = f"SELECT {column_value} FROM \"E-Mobility\".emo_historical WHERE {filter_clause};"
        
        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result}")

        return []


class ActionExecuteLimitQuery(Action):
   def name(self) -> Text:
      return "action_execute_limit_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()
      
        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        CARDINAL = tracker.get_slot("CARDINAL")
        user_input = tracker.latest_message['text']

        # first: convert kpi to its column name in database
        if kpi == 'Locations':
            kpi_value = 'no_total_locations'
        elif kpi == 'Charging stations':
            kpi_value = 'no_total_stations'
        elif kpi == 'Charging points':
            kpi_value = 'no_total_chargepoints'

        # second: check if it is top or below
        if "top" in user_input:
            q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};"
        elif "below" or "last" in user_input:
            q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum Limit {CARDINAL};"

        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result}")

        return []


class ActionExecuteWindowQuery(Action):
   def name(self) -> Text:
      return "action_execute_window_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()
      
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        number = tracker.get_slot("number")
        user_input = tracker.latest_message['text']
        places = tracker.latest_message['entities'][0]['value']

        # first: convert kpi to its column name in database
        if kpi == 'Locations':
            kpi_value = 'no_total_locations'
        elif kpi == 'Charging stations':
            kpi_value = 'no_total_stations'
        elif kpi == 'Charging points':
            kpi_value = 'no_total_chargepoints'

        q = f"SELECT SUM({kpi_value}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state IN ( 'Sachsen', 'Bayern','Brandenburg' ) GROUP BY state;"

        cur.execute(q)
        result = cur.fetchall()
        for i in result:
            dispatcher.utter_message(text=f"{i[0], i[1]}")

        return []

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