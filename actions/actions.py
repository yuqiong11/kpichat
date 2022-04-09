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
import datetime
import sys
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)
from time_mapping import CheckTime

from query_translator import QueryTranslator


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

    def validate_DATE(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate time value."""

        check_time = CheckTime()
        mapped_time = check_time.time_mapping(slot_value)

        if check_time.time_out_of_range(mapped_time):
            # time is out-of-range
            # user will be asked for the slot again
            dispatcher.utter_message(text="Oops, your wished timestamp is out of range.")
            return {"DATE": None}
        else:
            # validation succeeded, set the slot
            return {"DATE": slot_value}


class ActionQueryClarify(Action):

    def name(self) -> Text:
        return "action_query_clarify"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        place = tracker.get_slot("place")
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place is {place}")
        dispatcher.utter_message(text=f"time is {DATE}")
        dispatcher.utter_message(text=f"kpi is {kpi}")

        return []


class ActionResetSlots(Action):

    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("DATE", None), SlotSet("mapped_time", None), 
        SlotSet("max", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("desc", None),
        SlotSet("asc", None), SlotSet("le", None), SlotSet("ge", None), SlotSet("bet", None), SlotSet("CARDINAL", None)]

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
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place: {place}\n kpi: {kpi}\n time:{DATE}?",
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
        runs after intent agg_query.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        avg = tracker.get_slot("avg")
        # user_input = tracker.latest_message['text']

        translator = QueryTranslator()
        is_prediction = translator.kpi_is_prediction(DATE)
        q = translator.agg_query(kpi, place, DATE, max=max, min=min, avg=avg)
        dispatcher.utter_message(text=q)
        cur.execute(q)
        results = cur.fetchall()
        for result in results:
            if not is_prediction:
                dispatcher.utter_message(text=f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} is "+str(round(result[0]))+".")
            else:
                dispatcher.utter_message(text=f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} will be approximately "+str(round(result[0]))+".")
                dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is January 2022.")
        return []



class ActionExecuteGroupSortQuery(Action):
   def name(self) -> Text:
      return "action_execute_group_sort_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent group_sort_query
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        desc = tracker.get_slot("desc")
        asc = tracker.get_slot("asc")

        
        q = QueryTranslator.group_sort_query(kpi, place, DATE, desc=desc, asc=asc)

        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result[0]}")

        return []



class ActionExecuteFilterQuery(Action):
   def name(self) -> Text:
      return "action_execute_filter_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent filter_query
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        ge = tracker.get_slot("ge")
        le = tracker.get_slot("le")
        bet = tracker.get_slot("bet")
        user_input = tracker.latest_message['text']

        q = QueryTranslator.filter_query(kpi, place, DATE, user_input, ge=ge, le=le, bet=bet)
        
        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result}")

        return []


class ActionExecuteLimitQuery(Action):
   def name(self) -> Text:
      return "action_execute_limit_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent limit_query
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()
      
        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        CARDINAL = tracker.get_slot("CARDINAL")
        user_input = tracker.latest_message['text']

        q = QueryTranslator.limit_query(kpi, place, DATE, user_input, CARDINAL)

        cur.execute(q)
        result = cur.fetchall()
        dispatcher.utter_message(text=f"{result}")

        return []


class ActionExecuteWindowQuery(Action):
   def name(self) -> Text:
      return "action_execute_window_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent window_query
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()
      
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        number = tracker.get_slot("number")
        user_input = tracker.latest_message['text']
        places = tracker.latest_message['entities'][0]['value']

        q = QueryTranslator.window_query()

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


