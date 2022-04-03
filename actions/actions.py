# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict

import psycopg2
# importing sys
import sys
# adding target folder to the system path
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/own_models'
sys.path.insert(0, path)
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)
from time_mapping import convert_time
from kpi_mapping import kpi_mapping
from sql_mapping import cluster_sql_mapping, query_clusters
from sentence_transformer import output_template, default_params
from constants import state_list


class ValidateKpiForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_kpi_form"


    @staticmethod
    def places_db() -> List[Text]:
        """Database of supported places"""
        with open('./GPE_Germany.txt', 'r', encoding='utf8') as f:
            data = f.read()
            places = data.split('\n')

        return places

    def validate_place(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate place value."""

        if slot_value in self.places_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"place": slot_value}
        else:
            # validation failed, set this slot to None so that the
            # user will be asked for the slot again
            dispatcher.utter_message(text="Oops, this place was not found. I only recognize vaild place name within Germany.")
            return {"place": None}

class ActionConvertDate(Action):

    def name(self) -> Text:
        return "action_convert_date"

    def run(self, dispatcher, tracker, domain):
        DATE = tracker.get_slot("DATE")
        mapped_time = convert_time(DATE)                   
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
        return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("DATE", None), SlotSet("mapped_time", None), 
                SlotSet("max", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("desc", None),
                SlotSet("asc", None), SlotSet("le", None), SlotSet("ge", None), SlotSet("bet", None), SlotSet("CARDINAL", None),
                SlotSet("stored_intent", None),  SlotSet("stored_user_input", None)]

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

class ActionTemIntent(Action):

    def name(self) -> Text:
        return "action_tem_store"

    def run(self, dispatcher, tracker, domain):

        """
        action triggered directly after intent like agg_query, stores data for later use

        """
        # store user intent
        intent = tracker.latest_message['intent'].get('name')
        # store user input
        user_input = tracker.latest_message['text']

        # store indices of entities
        entities = tracker.latest_message['entities']

        for entity in entities:
            for k,v in entity.items():
                if v == 'kpi':
                    kpi_idx = {
                        'start': entity['start'],
                        'end': entity['end']
                    }                   
                  
                elif v == 'DATE':
                    DATE_idx = {
                        'start': entity['start'],
                        'end': entity['end']
                    }
                elif v == 'place':
                    place_idx = {
                        'start': entity['start'],
                        'end': entity['end']
                    }

        return [SlotSet("stored_intent", intent), SlotSet("stored_user_input", user_input), SlotSet("stored_entities_indices", {'kpi_idx': kpi_idx, 'DATE_idx': DATE_idx, 'place_idx': place_idx})]

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
        intent = tracker.get_slot("stored_intent")
        user_input = tracker.get_slot("stored_user_input")
        entities_indices = tracker.get_slot("stored_entities_indices")
        
        # intent = tracker.latest_message['intent'].get('name')
        

        # first: convert kpi to its column name in database
        kpi = kpi_mapping.get(f"{kpi}")

        # mask user input
        
        kpi_start, kpi_end = entities_indices.get('kpi_idx')['start'], entities_indices.get('kpi_idx')['end']
        place_start, place_end = entities_indices.get('place_idx')['start'], entities_indices.get('place_idx')['end']
        DATE_start, DATE_end = entities_indices.get('DATE_idx')['start'], entities_indices.get('DATE_idx')['end']
        kpi_raw = user_input[kpi_start:kpi_end]
        place_raw = user_input[place_start:place_end]
        DATE_raw = user_input[DATE_start:DATE_end]

        masked_query = user_input.replace(kpi_raw, "[kpi]")
        masked_query = user_input.replace(DATE_raw, "[mapped_time]")
        if place in state_list:
            masked_query = user_input.replace(place_raw, "[place_state]")
        else:
            masked_query = user_input.replace(place_raw, "[place_county]")

        # third: sql mapping
        q = output_template(masked_query, intent, **default_params)
        dispatcher.utter_message(text=q)
        # cur.execute(q)
        # result = cur.fetchall()
        # if len(result) == 1:
        #     dispatcher.utter_message(text=f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} is "+str(round(result[0][0])))

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