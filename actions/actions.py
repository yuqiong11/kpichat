# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
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

# class ActionChangeSlot(Action):

#     def name(self) -> Text:
#         return "action_change_slot"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         place = tracker.get_slot("place")
#         DATE = tracker.get_slot("DATE")
#         kpi = tracker.get_slot("kpi")
#         dispatcher.utter_message(text=f"place is {place}")
#         dispatcher.utter_message(text=f"time is {DATE}")
#         dispatcher.utter_message(text=f"kpi is {kpi}")

#         return []




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
        # return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("DATE", None), SlotSet("mapped_time", None), 
        # SlotSet("max", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("desc", None),
        # SlotSet("asc", None), SlotSet("le", None), SlotSet("ge", None), SlotSet("bet", None), SlotSet("CARDINAL", None)]
        return [AllSlotsReset()]

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
        dispatcher.utter_message(text=f"place: {place}\n kpi: {kpi}\n time: {DATE}",
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
    
        if results:
            for result in results:
                if len(result) == 1:
                    if not is_prediction:
                        dispatcher.utter_message(text=f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} is "+str(round(result[0]))+".")
                    else:
                        dispatcher.utter_message(text=f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} is "+str(round(result[0]))+".")
                        dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is March 2022.")
                else:
                    if not is_prediction:
                        dispatcher.utter_message(text=f"{result[1]} has the {max if max != None else ''}{min if min != None else ''} number of {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which is "+str(round(result[0]))+".")
                    else:
                        dispatcher.utter_message(text=f"{result[1]} has the {max if max != None else ''}{min if min != None else ''} number of {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which is "+str(round(result[0]))+".")
                        dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is March 2022.")
        else:
            dispatcher.utter_message(text="No results found for your query.")

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
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")

        translator = QueryTranslator()
        is_prediction = translator.kpi_is_prediction(DATE)
   
        q = translator.group_sort_query(kpi, place, DATE, desc=desc, asc=asc, max=max, min=min)
        print(q)

        cur.execute(q)
        results = cur.fetchall()
        res =""

        if results:
            for result in results:
                res += f"{result[1]}, {round(result[0])}\n"

            dispatcher.utter_message(text=res)

            if is_prediction:
                dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is March 2022.")

        else:
            dispatcher.utter_message(text="No results found for your query.")

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
        CARDINAL = tracker.get_slot("CARDINAL")
        ge = tracker.get_slot("ge")
        le = tracker.get_slot("le")
        bet = tracker.get_slot("bet")
        user_input = tracker.latest_message['text']
        translator = QueryTranslator()
        is_prediction = translator.kpi_is_prediction(DATE)

        q = translator.filter_query(kpi, place, DATE, ge=ge, le=le, bet=bet, CARDINAL=CARDINAL)
        
        cur.execute(q)
        results = cur.fetchall()
        res =""

        if results:

            if len(results) <= 20:
                for result in results:
                    res += f"{result[0]}, {round(result[1])}\n"
            else:
                res += f"In total {len(results)} returned. Here are the first 20 results:\n"
                results = results[:20]
                for result in results:
                    res += f"{result[0]}, {round(result[1])}\n"
                

            dispatcher.utter_message(text=res)
            if is_prediction:
                dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is March 2022.")

        else:
            dispatcher.utter_message(text="No results found for your query.")

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
        top = tracker.get_slot("top")
        bottom = tracker.get_slot("bottom")
        # user_input = tracker.latest_message['text']

        translator = QueryTranslator()
        is_prediction = translator.kpi_is_prediction(DATE)

        q = translator.limit_query(kpi, place, DATE, CARDINAL, top, bottom)

        cur.execute(q)
        results = cur.fetchall()

        res =""
        if results:
            for result in results:
                res += f"{result[1]}, {round(result[0])}\n"

            dispatcher.utter_message(text=res)
            if is_prediction:
                dispatcher.utter_message(text="Please be aware that this is a prediction based on past values. The latest timestamp is March 2022.")

        else:
            dispatcher.utter_message(text="No results found for your query.")

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
        place = tracker.get_slot("place")
        place_list = tracker.get_slot("place_list")


        translator = QueryTranslator()
        is_prediction = translator.kpi_is_prediction(DATE)
        q = translator.window_query(kpi, place, DATE, place_list)

        cur.execute(q)
        results = cur.fetchall()
        for result in results:
            dispatcher.utter_message(text=f"{result[0]}")

        return []

# establish postgresql connection
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

# coref start from here
class ActionCheckCoref(Action):
   def name(self) -> Text:
      return "action_check_coref"

   def run(self, dispatcher, tracker, domain):
        slots = tracker.current_slot_values()

        new_slot = tracker.latest_message.entities.keys()[0]
        # if ("above average" in user_input) or ("over average" in user_input) or ("below average" in user_input) or ("under average" in user_input):
        #     return [SlotSet("ge", None), SlotSet("bet", None), SlotSet("le", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("max", None),
        #             SlotSet("bottom", None), SlotSet("top", None), SlotSet("asc", None), SlotSet("desc", None)]        
        if new_slot == "max":
            return [SlotSet("min", None), SlotSet("avg", None)]
        elif new_slot == "min":
            return [SlotSet("max", None), SlotSet("avg", None)]
        elif new_slot == "avg":
            return [SlotSet("min", None), SlotSet("max", None)]
        elif new_slot == "desc":
            return [SlotSet("asc", None)]
        elif new_slot == "asc":
            return [SlotSet("desc", None)]
        elif new_slot == "le":
            return [SlotSet("ge", None), SlotSet("bet", None)]
        elif new_slot == "ge":
            return [SlotSet("le", None), SlotSet("bet", None)]
        elif new_slot == "bet":
            return [SlotSet("le", None), SlotSet("bet", None)]
        elif new_slot == "top":
            return [SlotSet("bottom", None)]
        elif new_slot == "bottom":
            return [SlotSet("top", None)]


class ActionStoreSlots(Action):
   def name(self) -> Text:
      return "action_store_slots"

   def run(self, dispatcher, tracker, domain):
        slots = tracker.current_slot_values()
        del slots["stored_slots"]
        return [SlotSet("stored_slots", slots)]       
            

class ActionResetSlotsExceptStored(Action):
   def name(self) -> Text:
      return "action_reset_slots_except_stored"

   def run(self, dispatcher, tracker, domain):
        stored_slots = tracker.get_slot("stored_slots")
        slots = tracker.current_slot_values()
        return_slots = []
        for slot_name in slots.keys():
            if slot_name != "stored_slots":
                return_slots.append(SlotSet(slot_name, None))
        return return_slots


class ActionSetStored(Action):
    def name(self) -> Text:
      return "action_set_stored"

    def run(self, dispatcher, tracker, domain):
        stored_slots = tracker.get_slot("stored_slots")
        new_slot = tracker.latest_message['entities'][0]['entity']
        if new_slot == "CARDINAL":
            new_slot = tracker.latest_message['entities'][1]['entity']

        return_slots = []

        if new_slot == "max":
            for slot, v in stored_slots.items():
                if slot in ("min", "avg"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "min":
            for slot, v in stored_slots.items():
                if slot in ("max", "avg"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "avg":
            for slot, v in stored_slots.items():
                if slot in ("max", "min"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v)) 
        elif new_slot == "desc":
            for slot, v in stored_slots.items():
                if slot == "asc":
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v))   
        elif new_slot == "asc":
            for slot, v in stored_slots.items():
                if slot == "desc":
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v))    
        elif new_slot == "le":
            for slot, v in stored_slots.items():
                if slot in ("ge", "bet"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot and slot != "CARDINAL":
                    return_slots.append(SlotSet(slot, v)) 
        elif new_slot == "ge":
            for slot, v in stored_slots.items():
                if slot in ("le", "bet"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot and slot != "CARDINAL":
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "bet":
            for slot, v in stored_slots.items():
                if slot in ("le", "ge", "CARDINAL"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v)) 
        elif new_slot == "top":
            for slot, v in stored_slots.items():
                if slot == "bottom":
                    return_slots.append(SlotSet(slot, None))
                elif slot not in (new_slot, "CARDINAL"):
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "bottom":
            for slot, v in stored_slots.items():
                if slot == "top":
                    return_slots.append(SlotSet(slot, None))
                elif slot not in (new_slot, "CARDINAL"):
                    return_slots.append(SlotSet(slot, v))
        else:
            for slot, v in stored_slots.items():
                if slot != new_slot:
                    return_slots.append(SlotSet(slot, v))    
        return return_slots
