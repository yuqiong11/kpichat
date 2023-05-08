# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# from ast import operator
# from concurrent.futures.process import _ExceptionWithTraceback
from typing import Any, Text, Dict, List, Optional
from numpy import result_type

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction, EventType, Restarted, UserUttered
from rasa_sdk.types import DomainDict

import psycopg2
import pymongo
import datetime
import sys

from utils.constants import PREDEFINED_KPI
from mappings.time_mapping import CheckTime
from mappings.synonym_mapping import PREDEFINED_KPI_MAPPING, predefined_kpi_mapping
from mappings.data_format_mapping import MapDataFormat

from backend.query_translator import QueryTranslator
from backend.db import QueryMethods
from backend.faqs import RetrieveAnswer
# from process_newKPI import ResolveKPIDefinition
# from New_KPI import new_kpi_list
from bson import BSON
from bson.objectid import ObjectId
from nearby_search import NearbySearch
from backend.process import AggQueryProcessor, CompareQueryProcessor, ChargerProviderQueryProcessor

from rapidfuzz import process, fuzz
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity
# extract latest month from database
MONTH_DICT = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }
sql_query = QueryMethods()
execute = 'SELECT TO_CHAR(update_timestamp, \'yyyy\'), TO_CHAR(update_timestamp, \'MM\') FROM \"E-Mobility\".emo_historical LIMIT 1'
results = sql_query.execute_sqlquery(execute)
# print(results)
# latest_month = results[0][0] + results[0][1]

# load faqs model and sentence embeddings
start_retrieve = RetrieveAnswer()

REQUESTED_SLOT = "requested_slot"
PATH = "./actions/Query_classification/bert_model"
SORRY_MESSAGE = "I'm very sorry but something went wrong😵‍💫​ Our team will take care of this issue soon🔧 Thanks for your patience!"
SORRY_MESSAGE_GER = "Es tut mir leid, es scheint etwas schief gelaufen zu sein😵‍💫​ Unser Team wird dieses Problem bald lösen🔧 Vielen dank für die Geduld!"

# if results[0][1][0] != 0:
#     PREDICTION_MSG = f"Please be aware that the source data usually lags and the latest available month is {MONTH_DICT[int(results[0][1])-1]+' '+results[0][0]}, so this is a prediction based on past values."
# elif results[0][1][1] != 1:
#     PREDICTION_MSG = f"Please be aware that the source data usually lags and the latest available month is {MONTH_DICT[int(results[0][1][1])-1]+' '+results[0][0]}, so this is a prediction based on past values."
# else:
#     PREDICTION_MSG = f"Please be aware that the source data usually lags and the latest available month is December {results[0][0]}, so this is a prediction based on past values."



# ----------------------------------------
# set language
# ----------------------------------------
# class SetLanguage(Action):
#     def name(self) -> Text:
#         return "action_set_language"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
#     ) -> List[EventType]:
#         welcome_intent = tracker.latest_message['intent'].get('name')
#         if welcome_intent == "welcome_message_en":
#             return [SlotSet("language", "english")]
#         elif welcome_intent == "welcome_message_ge":
#             return [SlotSet("language", "german")]
#         else: 
#             return [SlotSet("language", "english")]

# ----------------------------------------
# service mapping
# ----------------------------------------

class ServiceMapping(Action):
    def name(self) -> Text:
        return "action_service_mapping"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        # user chooses by number
        user_input = tracker.latest_message['text']
        if user_input in ('0','1','2','3','4'):
            if user_input == '0':
                return [SlotSet("service", 0)]
            elif user_input == '1':
                return [SlotSet("service", 1)]
            elif user_input == '2':
                return [SlotSet("service", 2)]        
            elif user_input == '3':
                return [SlotSet("service", 3)]
            elif user_input == '4':
                return [SlotSet("service", 4)]

        # user chooses by inputting the query
        user_intent = tracker.latest_message['intent'].get('name')
        if user_intent == "KPI_query":
            return [SlotSet("service", 1)]
        elif user_intent == "nearby_search":
            return [SlotSet("service", 2)]
        elif user_intent == "E-Mobility FAQs":
            return [SlotSet("service", 3)]
        elif user_intent == "main_menu":
            return [SlotSet("service", 4)]

        
        return []
# ----------------------------------------
# validate forms
# ----------------------------------------

class ValidateKpiForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_kpi_form"


    @staticmethod
    def places_db() -> List[Text]:
        """Database of supported places"""
        with open('./lookup/GPE_Germany.txt', 'r', encoding='utf8') as f:
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

        geo_level = tracker.get_slot("geo_level")

        if geo_level:
            return {"place": "not required"} 
                
        elif len(slot_value) == 1:
            if slot_value[0] in self.places_db() or slot_value:
                # validation succeeded, set the value of the "place" slot to value
                return {"place": slot_value}
            else:
                # validation failed, set this slot to None so that the
                # user will be asked for the slot again
                dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                return {"place": None}
        else:
            if slot_value[0] in self.places_db():
                if slot_value[1] in self.places_db():                    
                    return {"place": slot_value}
                else:
                    dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                    return {"place": None}                    
            else:
                dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                return {"place": None}

    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate time value."""

        charger_type = tracker.get_slot("charger_type")
        operator = tracker.get_slot("operator")

        if charger_type or operator:
            has_prediction = False
        else:
            has_prediction = True

        for v in slot_value:
            check_time = CheckTime()
            mapped_time = check_time.time_mapping(v, False, True)

            if check_time.time_out_of_range(mapped_time, has_prediction):
                # time is out-of-range
                # user will be asked for the slot again
                dispatcher.utter_message(text="Oops, you have inputted an invalid time or your wished time is out of range.")
                if has_prediction:
                    dispatcher.utter_message(text="You can choose a time between January 2017 and December 2023.")
                else:
                    dispatcher.utter_message(text="If you are looking for info about fast/normal chargepoints or operators, enter a time before January 2023.")

                return {"time": None}
            else:
                continue
        
        return {"time": slot_value}

    def validate_kpi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate kpi value."""

        operator = tracker.get_slot("operator")

        if operator:
            return {"kpi": "not required"} 

        

class ValidateArgsForm(FormValidationAction):
    # not used for now ###############################################

    # def __init__(self):
    #     self.required_info = required_info

    def name(self) -> Text:
        return "validate_args_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Text]:
        # required_slots = tracker.get_slot("args_to_be_asked")
        # uptimed_slots = domain_slots.copy()
        # uptimed_slots = required_slots
        print('domain_slots: ',domain_slots)
        args_to_be_asked = tracker.slots.get("args_to_be_asked")
        num_args = len(args_to_be_asked)

        if num_args == 1:
            return domain_slots
        else:
            if num_args == 2:
                additional_slots=["arg_2"]
            if num_args >= 3:
                # now the maximum number of args are set to 3
                additional_slots=["arg_2", "arg_3"]

            return additional_slots + domain_slots

# -----------------------------------------------
# ask for next slots
# -----------------------------------------------
class AskForARG1(Action):
    def name(self) -> Text:
        return "action_ask_arg_1"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        dispatcher.utter_message(text=f"What is the {args_to_be_asked[0]} of {place[0]} {'in' if time[0] != 'now' else ''} {time[0]}? Enter the number using the format '123' for integer or '123.45' for decimal. If you don't know or don't want to answer it, please type 'skip'.")
        return []

class AskForARG2(Action):
    def name(self) -> Text:
        return "action_ask_arg_2"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        dispatcher.utter_message(text=f"What is the {args_to_be_asked[1]} of {place[0]} {'in' if time[0] != 'now' else ''} {time[0]}? If you don't know or don't want to answer it, please type 'skip'.")
        return []

class AskForARG3(Action):
    def name(self) -> Text:
        return "action_ask_arg_3"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        dispatcher.utter_message(text=f"What is the {args_to_be_asked[2]} of {place[0]} {'in' if time[0] != 'now' else ''} {time[0]}? If you don't know or don't want to answer it, please type 'skip'.")
        return []

class AskForKPI(Action):
    def name(self) -> Text:
        return "action_ask_kpi"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # get list of userdefined kpis
        with open('./lookup/New_KPI.txt', 'r', encoding='utf8') as f:
            data = f.read()
            new_kpi_list = data.split('\n')
        my_str = "Userdefined KPIs:  \n "
        for kpi in new_kpi_list:
            my_str += f"{kpi}  \n "

        # get user intent
        intent= tracker.latest_message['intent'].get('name') 

        if intent == 'charger_type':
            buttons = [
            {"title": "fast Charging_stations","payload": ['/inform{{"kpi":"Charging stations"}}, /inform{{"charger_type":"fast"}}']},
            {"title": "normal Charging_stations", "payload": ['/inform{{"kpi":"Charging stations"}}, /inform{{"charger_type":"normal"}}']},        
            ]
        elif intent == 'charger_operator':
            buttons = [
            {"title": "Charging_station_operators", "payload": '/inform{{"operator":"operator"}}'},
            ]
        else:
            buttons = [
            {"title": "Location","payload": '/inform{{"kpi":"Locations"}}'},
            {"title": "Charging_stations", "payload": '/inform{{"kpi":"Charging stations"}}'},
            {'title':"Charging_points", "payload": '/inform{{"kpi":"Charging points"}}'},
            {"title": "Cars_per_charging_point","payload": '/inform{{"kpi":"Cars_per_charging_point"}}'},
            {"title": "Charging_points_per_1,000_cars", "payload": '/inform{{"kpi":"Charging_points_per_1,000_cars"}}'},
            {'title':"Percentage_of_target", "payload": '/inform{{"kpi":"Percentage_of_target"}}'},        
            ]
    
        dispatcher.utter_message(text=f"Which KPI are you interested in? Choose one from the predefined KPIs or enter a userdefined KPI or a new KPI as you like. Please also enter the kpi again even if it was already included in the query.")
        dispatcher.utter_message(buttons=buttons, text=my_str)
        return []
# -----------------------------------------------
# util actions
# -----------------------------------------------

class ActionQueryClarify(Action):

    def name(self) -> Text:
        return "action_query_clarify"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place is {place}  \ntime is {time}  \nkpi is {kpi}")
        return []

# class ActionResetSlots(Action):

#     def name(self) -> Text:
#         return "action_reset_slots"

#     def run(self, dispatcher, tracker, domain):
#         # return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("time", None), SlotSet("mapped_time", None), 
#         # SlotSet("max", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("desc", None),
#         # SlotSet("asc", None), SlotSet("le", None), SlotSet("ge", None), SlotSet("bet", None), SlotSet("cardinal", None)]
#         return [AllSlotsReset()]

class ActionResetSlotsExceptService(Action):

    def name(self) -> Text:
        return "action_reset_slots_except_service"

    def run(self, dispatcher, tracker, domain):
        slots = tracker.current_slot_values()
        return_slots = []
        for slot_name in slots.keys():
            if slot_name not in ("service", "language"):
                return_slots.append(SlotSet(slot_name, None))
        return return_slots

class ActionSlotCheck(Action):

    def name(self) -> Text:
        return "action_slot_check"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"place: {place} \nkpi: {kpi} \ntime:{time}")

        return []


class ActionChangeSlot(Action):

    def name(self) -> Text:
        return "action_change_slot"

    def run(self, dispatcher, tracker, domain):
        # deal with entry like 'kpi_name: charging_points_per_population'
        text = tracker.latest_message['text']
        slot_name, _, slot_value = text.partition(':')
        return [SlotSet(slot_name, slot_value[1:])]

class ActionQueryConfirm(Action): 

    def name(self) -> Text:
        return "action_query_confirm"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")
        kpi = tracker.get_slot("kpi")
        operator = tracker.get_slot("operator")
        charger_type = tracker.get_slot("charger_type")
        max_ = tracker.get_slot("max")
        min_ = tracker.get_slot("min")
        avg_ = tracker.get_slot("avg")
        geo_level = tracker.get_slot("geo_level")
        # if charger_type:
        #     dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type} {kpi}",
        #     buttons= [
        #     {"title": "yes","payload": "/affirm"},
        #     {"title": "no", "payload": "/deny"}
        #     ])
        # elif operator:
        #     dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: Charging_station_operators",
        #     buttons= [
        #     {"title": "yes","payload": "/affirm"},
        #     {"title": "no", "payload": "/deny"}
        #     ])
        # else:
        if operator:
            if geo_level == "germany" and place == None:
                if max_:
                    dispatcher.utter_message(text=f"place: Germany  \ntime: {time[0] if len(time)==1 else time}  \nrank: {max_}",
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ])
                elif min_:
                    dispatcher.utter_message(text=f"place: Germany  \ntime: {time[0] if len(time)==1 else time}  \nrank: {min_}",                
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ]) 
                else:
                    dispatcher.utter_message(text=f"place: Germany  \ntime: {time[0] if len(time)==1 else time}", 
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ])                     
            else:
                if max_:
                    dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \ntime: {time[0] if len(time)==1 else time}  \nrank: {max_}",
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ])
                elif min_:
                    dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \ntime: {time[0] if len(time)==1 else time}  \nrank: {min_}",                
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ]) 
                else:
                    dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \ntime: {time[0] if len(time)==1 else time}", 
                    buttons= [
                    {"title": "yes","payload": "/affirm"},
                    {"title": "no", "payload": "/deny"}
                    ])                                            
        elif geo_level:
            if max_:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type if charger_type and kpi else ''} {kpi}  \ntime: {time[0] if len(time)==1 else time}  \ncondition: {max_}",
                buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
                ])
            elif min_:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type if charger_type and kpi else ''} {kpi}  \ntime: {time[0] if len(time)==1 else time}  \ncondition: {min_}",
                buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
                ])
            elif avg_:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type if charger_type and kpi else ''} {kpi}  \ntime: {time[0] if len(time)==1 else time}  \ncondition: {avg_}",
                buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
                ])
        else:
            dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type if charger_type and kpi else ''} {kpi}  \ntime: {time[0] if len(time)==1 else time}",
            buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
            ])
        return []

class ActionContinueOptions(Action):
    def name(self) -> Text:
        return "action_continue_options"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        service = tracker.get_slot("service")

        if service in (1,2,3):
            options_mapping = {
                1: 'Continue asking',
                2: 'Search again',
                3: 'Ask another question'
            }

            dispatcher.utter_message(text=f"Do you want to...?",
            buttons= [
                {"title": f"{options_mapping[service]}","payload": "/continue"},
                {"title": "Back to main menu", "payload": "/main_menu"}
            ])
        # if service in (1,2,3):
        #     options_mapping = {
        #         1: 'Continue asking',
        #         2: 'Search again',
        #         3: ['Have a FAQ', 'Add a FAQ']
        #     }
        #     if service == 3:
        #         dispatcher.utter_message(text=f"Do you want to...?",
        #         buttons= [
        #             {"title": f"{options_mapping[service][0]}","payload": '/continue{"identifier_faqs":false}'},
        #             {"title": f"{options_mapping[service][1]}","payload": '/continue{"identifier_faqs":true}'},                
        #             {"title": "Back to main menu", "payload": "/main_menu"}
        #         ])

        #     else:
        #         dispatcher.utter_message(text=f"Do you want to...?",
        #         buttons= [
        #             {"title": f"{options_mapping[service]}","payload": "/continue"},
        #             {"title": "Back to main menu", "payload": "/main_menu"}
        #         ])

        elif service == 4:
            dispatcher.utter_message(text=f"Do you want to...?", buttons=[{"title": "Back to main menu", "payload": "/main_menu"}])

        else:
            dispatcher.utter_message(text=f"Do you want to...?",
            buttons= [
                {"title": 'Continue this service',"payload": "/continue"},
                {"title": "Back to main menu", "payload": "/main_menu"}
            ])

        return []
# --------------------------------------------
# excute queries in postgresql
# --------------------------------------------

class ActionKPIList(Action):
   def name(self) -> Text:
      return "action_kpi_list"

   def run(self, dispatcher, tracker, domain):

        """
        returns a list of predefined KPIs and userdefined KPIs
        
        """
        dispatcher.utter_message(text="KPIs:  \n fast/normal charging points  \n charging_points_per_1000_cars  \n percentage_of_target  \n operators")

        # with open('./lookup/New_KPI.txt', 'r', encoding='utf8') as f:
        #     data = f.read()
        #     new_kpi_list = data.split('\n')
        
        # if new_kpi_list is None:
        #     kpi_str = "(empty)"

        # else:
        #     kpi_str = "Userdefined KPIs:  \n "
        #     for kpi in new_kpi_list:
        #         kpi_str += f"{kpi}  \n "

        # dispatcher.utter_message(text=kpi_str)   

        # hints = "You can start asking me your query. Follow the examples below if you don't know how to ask properly:  \n For predefined KPI:  \n 1.What is the number of charging\_points in Berlin in July 2022?  \n 2.Which county had the highest Percentage\_of\_target in March 2021?  \n 3.What is the increased value of Cars\_per\_charging\_point in Bayern from 01.2022 to 05.2022?  \n For userdefined KPI:  \n What is charging_points_per_person in Germany in August 2022?  \n There are many more queries available. Explore and find them out😄 \n To let the chatbot understand you better, add '\_' between words for KPI names."     
        hints = "Start asking me queries! Here's an example for what you can ask: What was the number of charging points in Berlin in July 2022?"     

        dispatcher.utter_message(text=hints)  
        return []


class ActionExecuteKPIQuery(Action):
   def name(self) -> Text:
      return "action_execute_kpi_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent KPI_query.

        Types of queries:

        1) query at a timepoint
        2) query for a time interval

        Subtypes of queries of above queries:

        1) aggregate query (value, max/min/avg/chargertype)
        2) compare query (berlin and hamburg?)
        3) charger provider query
        
        """
  
        query = tracker.get_slot("query")

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        time = tracker.get_slot("time")
        geo_level = tracker.get_slot("geo_level")
        max_ = tracker.get_slot("max")
        min_ = tracker.get_slot("min")
        avg_ = tracker.get_slot("avg")
        increase = tracker.get_slot("increase")
        charger_type = tracker.get_slot("charger_type")
        operator = tracker.get_slot("operator")
        q_type = tracker.get_slot("q_type")

        # if len(time) == 1:
        #     converted_month = translator.time_mapping(time[0], False)
        # elif len(time) == 2:
        #     converted_month = translator.time_mapping(time[1], False)

        # if converted_month >= latest_month:
        #     is_prediction = True
        # else:
        #     is_prediction = False

        # aggregate query (value, max/min/avg)
        # slots: place, kpi, month, (max, min, avg)
        if time:
            if operator:
                processor = ChargerProviderQueryProcessor(query=query,place=place, kpi=kpi, time=time, max=max_, min=min_, geo_level=geo_level, increase=increase,charger_type=charger_type,operator=operator, q_type=q_type)
                # q = translator.charger_provider(kpi, place, time, max=max_, min=min_, avg=avg, increase=increase)
            # elif cardinal and geo_level:
            #     processor = LimitQueryProcessor(text, place=place, kpi=kpi, time=time, geo_level=geo_level, max=max_, min=min_, avg=avg,increase=increase,charger_type=charger_type,operator=operator, cardinal=cardinal, q_type=q_type)
                # q = translator.limit(kpi, place, time, max=max_, min=min_, avg=avg, increase=increase)
            else:
                if len(place) > 1:
                    processor = CompareQueryProcessor(query=query,place=place, kpi=kpi, time=time, increase=increase,charger_type=charger_type, q_type=q_type)
                else:
                    processor = AggQueryProcessor(query=query,place=place, kpi=kpi, time=time,  max=max_, min=min_, avg=avg_, geo_level=geo_level, increase=increase,charger_type=charger_type, q_type=q_type)

                # q = translator.aggregate(kpi, place, time, max=max_, min=min_, avg=avg, increase=increase)
        
        dispatcher.utter_message(text=processor.run_response())
        return []
        # limit query (top 3/4/5/...)
        # slots: place, kpi, month, (max, min, avg)
        
        # if len(q) == 1:
        #     results_1 = make_query.execute_sqlquery(q[0])
        # else:
        #     # make_query.execute_sqlquery(q[0]) -> [(Decimal('6418.4646875688928426'), 'Bayern')]
        #     results_1, results_2 = make_query.execute_sqlquery(q[0])[0], make_query.execute_sqlquery(q[1])[0]

        # if q_type == "ask-number":
        #     if not avg:
        #         if kpi == 'Charging_points':
        #             text = f"The number of {kpi} in {place[0]} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({round(100*results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
        #         else:
        #             text = f"The {kpi} in {place[0]} {'' if time == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time == 'now' else 'was' } "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."            

        #     else:
        #         if len(place) == 1:
        #             if kpi == 'Charging_points':
        #                 text = f"The {avg} number of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
        #             else:
        #                 text = f"The {avg} {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0],1))+'%'+"."

        #         else:
        #             if kpi == 'Charging_points':
        #                 text = f"The {avg} number of {kpi} of {place[0]} in {place[1]} {'' if time[0] == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
        #             else:
        #                 text = f"The {avg} {kpi} of {place[0]} in {place[1]} {'' if time[0] == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."

        # elif q_type == "ask-place":
        #     if len(place) == 1:
        #         if kpi == 'Charging_points':
        #             text = f"{results_1[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was'} "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."   
        #         else:
        #             if len(time) != 1:
        #                 text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0][0]))+"."              
        #             else:
        #                 # results_1  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
        #                 print("results_1 ", results_1)
        #                 text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0][0]))+"."
        #         else:
        #             if not increase:
        #                 text = f"{results_1[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time == 'now' else 'was'} "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."

        #     else:
        #         if kpi == 'Charging_points':
        #             text = f"{results_1[1]} in {place[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
        #             else:
        #                 if len(time) != 1:
        #                     text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0]))+"."
        #                 else:
        #                     text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0]))+"."
        #         else:
        #             text = f"{results_1[1]} in {place[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was' }"+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        # else:
        #     # general template that handles wrong classification
        #     text = f"{kpi}  is "+str(round(results_1[0]))  



        # try:

        #     make_query = QueryMethods()
            
        #     # mapped_kpi = predefined_kpi_mapping(PREDEFINED_KPI_MAPPING, kpi)

        #     # 

        #     q = translator.agg_query(kpi, place, time, max=max, min=min, avg=avg, increase=increase)

        #     if len(q) == 1:
        #         results_1 = make_query.execute_sqlquery(q[0])

        #     else:
        #         # make_query.execute_sqlquery(q[0]) -> [(Decimal('6418.4646875688928426'), 'Bayern')]
        #         results_1, results_2 = make_query.execute_sqlquery(q[0])[0], make_query.execute_sqlquery(q[1])[0]

        #     # agg_query has q_type 'ask-number' or 'ask-place'
        #     if q_type == "ask-number":
        #         if not avg:
        #             if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
        #                 if not increase:
        #                     text = f"The number of {kpi} in {place[0]} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({round(100*results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
        #                 else:
        #                     if len(time) != 1:
        #                         # e.g. increase from 2019 to 2021
        #                         text = f"The increase of {kpi} in {place[0]} from {time[0]} to {time[1]} was "+str(round(results_1[0][0]))+ "."
        #                     else:
        #                         # e.g. increase last year
        #                         text = f"The increase of {kpi} in {place[0]} in {time[0]} was "+str(round(results_1[0][0]))+"."
        #             else:
        #                 if not increase:
        #                     text = f"The {kpi} in {place[0]} {'' if time == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time == 'now' else 'was' } "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."            
        #                 else:
        #                     if len(time) != 1:
        #                         text = f"The increase of {kpi} in {place[0]} from {time[0]} to {time[1]} was "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."        
        #                     else:
        #                         text = f"The increase of {kpi} in {place[0]} in {time[0]} was "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #         else:
        #             if len(place) == 1:
        #                 if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
        #                     if not increase:
        #                         text = f"The {avg} number of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
        #                     else:
        #                         if len(time) != 1:
        #                             text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} from {time[0]} to {time[1]} was "+str(round(results_1[0][0]))+"."
        #                         else:
        #                             text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} at {time[0]} was "+str(round(results_1[0][0]))+"."
        #                 else:
        #                     if not increase:
        #                         text = f"The {avg} {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0],1))+'%'+"."
        #                     else:
        #                         if len(time) != 1:
        #                             text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} from {time[0]} to {time[1]} was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #                         else:
        #                             text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if time[0] == 'now' else 'in'} {time[0]} was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #             else:
        #                 if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
        #                     if not increase:
        #                         text = f"The {avg} number of {kpi} of {place[0]} in {place[1]} {'' if time[0] == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
        #                     else:
        #                         if len(time) != 1:
        #                             text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} from {time[0]} to {time[1]} was "+str(round(results_1[0][0]))+"."
        #                         else:
        #                             text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} in {time[0]} was "+str(round(results_1[0][0]))+"."
        #                 else:
        #                     if not increase:
        #                         text = f"The {avg} {kpi} of {place[0]} in {place[1]} {'' if time[0] == 'now' else 'in'} in {time[0]} {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #                     else:
        #                         if len(time) != 1:
        #                             text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} from {time[0]} to {time[1]} was "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."   
        #                         else:
        #                             text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} in {time[0]} was "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #     elif q_type == "ask-place":
        #         if len(place) == 1:
        #             if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
        #                 if not increase:
        #                     text = f"{results_1[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was'} "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."   
        #                 else:
        #                     if len(time) != 1:
        #                         text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0][0]))+"."              
        #                     else:
        #                         # results_1  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
        #                         print("results_1 ", results_1)
        #                         text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0][0]))+"."
        #             else:
        #                 if not increase:
        #                     text = f"{results_1[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time == 'now' else 'was'} "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #                 else:
        #                     if len(time) != 1:
        #                         text = f"{results_1[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"."
        #                     else:
        #                         text = f"{results_1[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"." 
        #         else:
        #             if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
        #                 if not increase:
        #                     text = f"{results_1[1]} in {place[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
        #                 else:
        #                     if len(time) != 1:
        #                         text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0]))+"."
        #                     else:
        #                         text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0]))+"."
        #             else:
        #                 if not increase:
        #                     text = f"{results_1[1]} in {place[1]} {'has' if time[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if time[0] == 'now' else 'in'} {time[0]}, which {'is' if is_prediction or time[0] == 'now' else 'was' }"+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #                 else:
        #                     if len(time) != 1:
        #                         text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {time[0]} to {time[1]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #                     else:
        #                         text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {time[0]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
        #     else:
        #         # (not perfect)general template that handles wrong classification
        #         text = f"{kpi}  is "+str(round(results_1[0]))                               


        #     dispatcher.utter_message(text=text)

        #     if is_prediction:
        #         dispatcher.utter_message(text=PREDICTION_MSG)

        # except Exception as e:
        #     print("action_agg_query:",e)
        #     dispatcher.utter_message(text=SORRY_MESSAGE)

class ActionChargerTypeQuery(Action):

    def name(self) -> Text:
        return "action_execute_charger_type_query"

    def run(self, dispatcher, tracker, domain):
        kpi = tracker.get_slot("kpi")
        charger_type = tracker.get_slot("charger_type")
        place = tracker.get_slot("place")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        avg = tracker.get_slot("avg")
        q_type = tracker.get_slot("q_type") 
        try:
            make_query = QueryMethods()
            translator = QueryTranslator()

            q = translator.charger_type_query(place, charger_type, max=max, min=min, avg=avg)
            print("q ", q)

            if len(q) == 1:
                results_1 = make_query.execute_sqlquery(q[0])
            else:
                results_1, results_2 = make_query.execute_sqlquery(q[0]), make_query.execute_sqlquery(q[1])
                print('result_1', results_1[0])
                print('result_2', results_2[0])

            if q_type == "ask-number":
                if not avg:
                    text = f"The number of {charger_type} {kpi} in {place[0]} is "+str(round(results_1[0][0]))+ f"({round(100*results_1[0][0]/results_2[0][0], 2)}% of the total {charger_type} charging stations in Germany)"+"."
                else:
                    if len(place) == 1:
                        text = f"The {avg} number of {charger_type} {kpi} of a {'state' if 'state' in place[0].lower() else 'county'} is "+str(round(results_1[0][0]))+"."
                    else:
                        text = f"The {avg} number of {charger_type} {kpi} of {place[0]} in {place[1]} is "+str(round(results_1[0][0]))+"."
            elif q_type == "ask-place":
                if len(place) == 1:
                    text = f"{results_1[0][0]} has the {max if max else ''}{min if min else ''} number of {charger_type} {kpi}, which is "+str(round(results_1[0][1]))+ f"({100*round(results_1[0][1]/results_2[0][0], 2)}% of the total {charger_type} charging stations in Germany)"+"."   
                else:
                    text = f"{results_1[0][1]} in {place[1]} has the {max if max else ''}{min if min else ''} number of {charger_type} {kpi}, which is "+str(round(results_1[0][0]))+ f"({round(results_1[0][0]/results_2[0][0], 2)}% of the total {charger_type} charging stations in Germany)"+"."

            else:           
                text = f"{kpi} is "+str(round(results_1[0][0]))

            dispatcher.utter_message(text=text)
        except Exception as e:
            print("action_execute_charger_type_query:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)
        return []

class ActionChargerOperatorQuery(Action):

    def name(self) -> Text:
        return "action_execute_charger_operator_query"

    def run(self, dispatcher, tracker, domain):
        kpi = tracker.get_slot("kpi")
        operator = tracker.get_slot("operator")
        place = tracker.get_slot("place")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        q_type = tracker.get_slot("q_type") 
        try:
            make_query = QueryMethods()
            translator = QueryTranslator()

            # response1: There are 100 operators in germany/berlin/sachsen, here are the top 20
            # response2: The strongest/weakest operator in germany/berlin/sachsen is allego with 700 charging points(10% of the total in Germany)

            q = translator.charger_operator_query(place, max=max, min=min)

            if len(q) == 1:
                results_1 = make_query.execute_sqlquery(q[0])
            else:
                # all the queries return 2 results 
                results_1, results_2 = make_query.execute_sqlquery(q[0]), make_query.execute_sqlquery(q[1])

            text = ""
            if q_type == "ask-provider":
                if max or min:
                    print('687',results_1)
                    print('688',results_2)
                    text = f"The {'strongest' if max else 'weakest'} operator in {place[0]} is {results_1[0]} with {results_1[1]} ({100*round(results_1[1]/results_2[0], 2)}% of the total in Germany)" 
                else:
                    length_results = len(results_1)
                    if length_results > 20:
                        text = f"There are {len(results_1)} operators in {place[0]}, here are the top 20:  \n"
                        for result in results_1[:20]:
                            text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}%)  \n"
                    else:
                        text = f"There are {len(results_1)} operators in {place[0]}:  \n"
                        for result in results_1:
                            text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}%)  \n"                
                        
                    text += "*The number shows the number of charging stations each operator owns, in brackets is the percentage of it to the total in Germany."
                    dispatcher.utter_message(text=text)
            else:           
                for result in results_1:
                    print("results_2", results_2)
                    text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}% of the total in Germany)  \n"    

            dispatcher.utter_message(text=text)
        except Exception as e:
            print("action_execute_charger_operator_query:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)
        return []


class ActionExecuteLimitQuery(Action):
   def name(self) -> Text:
      return "action_execute_limit_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent limit_query
        
        """
        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        time = tracker.get_slot("time")
        cardinal = tracker.get_slot("cardinal")
        top = tracker.get_slot("top")
        bottom = tracker.get_slot("bottom")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        increase = tracker.get_slot("increase")
        q_type = tracker.get_slot("q_type") 
        # try:
        translator = QueryTranslator()
        make_query = QueryMethods()
        if len(time) == 1:
            converted_month = translator.time_mapping(time[0])
            if converted_month >= latest_month:
                is_prediction = True
            else:
                is_prediction = False

        # in case the intent 'agg' was wrongly classified as 'limit
        if not cardinal:
            cardinal = [1]

        q = translator.limit_query(kpi, place, time, cardinal, top, bottom, increase, max, min)
        print('limit: ', q)

        results = make_query.execute_sqlquery(q[0])

        if q_type == "ask-place":
            res =""
            if results:
                for result in results:
                    print('actions.py line 885: ', result)
                    res += f"{result[1]}, {round(result[0]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                dispatcher.utter_message(text=res)
                if is_prediction:
                    dispatcher.utter_message(text=PREDICTION_MSG)

            else:
                dispatcher.utter_message(text="No results found for your query.")

        else:
            res =""
            if results:
                for result in results:
                    res += f"{result[1]}, {round(result[0]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                dispatcher.utter_message(text=res)
                if is_prediction:
                    dispatcher.utter_message(text=PREDICTION_MSG)

            else:
                dispatcher.utter_message(text="No results found for your query.")

    
        # except Exception as e:
        #     print("action_execute_limit_query:",e)
        #     print("q:", q)
        #     print("results:",results)
        #     dispatcher.utter_message(text=SORRY_MESSAGE)
        return []

# --------------------------------------------
# coref start from here
# --------------------------------------------

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
            if slot_name not in ("stored_slots", "language"):
                return_slots.append(SlotSet(slot_name, None))
        return return_slots

class ActionSetStored(Action):
    def name(self) -> Text:
      return "action_set_stored"

    def run(self, dispatcher, tracker, domain):
        stored_slots = tracker.get_slot("stored_slots")
        print(tracker.latest_message['entities'])
        new_slot = tracker.latest_message['entities'][0]['entity']
        # if new_slot == "cardinal":
        #     new_slot = tracker.latest_message['entities'][1]['entity']

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
                elif slot != new_slot and slot != "cardinal":
                    return_slots.append(SlotSet(slot, v)) 
        elif new_slot == "ge":
            for slot, v in stored_slots.items():
                if slot in ("le", "bet"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot and slot != "cardinal":
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "bet":
            for slot, v in stored_slots.items():
                if slot in ("le", "ge", "cardinal"):
                    return_slots.append(SlotSet(slot, None))
                elif slot != new_slot:
                    return_slots.append(SlotSet(slot, v)) 
        elif new_slot == "top":
            for slot, v in stored_slots.items():
                if slot == "bottom":
                    return_slots.append(SlotSet(slot, None))
                elif slot not in (new_slot, "cardinal"):
                    return_slots.append(SlotSet(slot, v))
        elif new_slot == "bottom":
            for slot, v in stored_slots.items():
                if slot == "top":
                    return_slots.append(SlotSet(slot, None))
                elif slot not in (new_slot, "cardinal"):
                    return_slots.append(SlotSet(slot, v))
        else:
            for slot, v in stored_slots.items():
                if slot != new_slot:
                    return_slots.append(SlotSet(slot, v))    
        return return_slots

# -----------------------------------------------
# add knowledge(ask quiz)
# -----------------------------------------------
class ActionCheckQuiz(Action):
    def name(self) -> Text:
        return "action_check_quiz"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        try:
            make_query = QueryMethods()
            # get one random document from Questionbase
            result = make_query.random_access("Questionbase")
            if result:
                return [SlotSet("quiz_question", result)]
        except Exception as e:
            print("action_check_quiz:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)
        return [] 

class AskForQuiz1(Action):
    def name(self) -> Text:
        return "action_ask_quiz_1"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        quiz = tracker.get_slot("quiz_question")
        if quiz:
            dispatcher.utter_message(text=f"What is the {quiz['name']} of {quiz['place']} in {quiz['time']}? Enter the number using the format '123' for integer or '123.45' for decimal. If you don't know or don't want to answer it, please type 'skip'. ")

class NoQuiz(Action):
    def name(self) -> Text:
        return "action_no_quiz"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text=f"At the moment we have run out of questions😉. ")

# ------------------------------------------------------
# Below are the actions of self-learning
# ------------------------------------------------------

class ActionSaveNameLookup(Action):

    def name(self) -> Text:
        return "action_save_kpi_name_lookup"

    def run(self, dispatcher, tracker, domain):
        # get the slot
        kpi_name = tracker.get_slot("kpi_name")

        # add it to list
        # new_kpi_list = new_kpi_list.append(kpi_name)

        # write it into the file
        with open('./lookup/New_KPI.txt', 'a') as f:
            f.write(str(kpi_name)+'\n')

class ActionNewKPIConfirm(Action): 

    def name(self) -> Text:
        return "action_new_kpi_confirm"

    def run(self, dispatcher, tracker, domain):
        kpi_name = tracker.get_slot("kpi_name")
        kpi_definition = tracker.get_slot("kpi_definition")
        dispatcher.utter_message(text=f"kpi_name: {kpi_name}  \n kpi_definition: {kpi_definition}",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])
        return []

class ActionDefineKPIFinished(Action):

    def name(self) -> Text:
        return "action_define_kpi_finished"

    def run(self, dispatcher, tracker, domain):
        kpi_name = tracker.get_slot("kpi_name")
        kpi_definition = tracker.get_slot("kpi_definition")

        try:
            # save it in mongodb
            make_query = QueryMethods()
            client = make_query.set_mongodb_connect()
            db = client['emobility']
            new_kpi_definition = db['new_kpi_definition']
            new_kpi_definition.insert_one({"kpi_name": kpi_name, "kpi_definition": kpi_definition})
            dispatcher.utter_message(text="Good. I have put it in the knowledgebase.")

        except Exception as e:
            print(e)
            dispatcher.utter_message(text=SORRY_MESSAGE)

        return 

class ActionCheckPredefinedAndUserdefined(Action):

    def name(self) -> Text:
        return "action_check_predefined_and_userdefined"

    
    def run(self, dispatcher, tracker, domain):
        kpi = tracker.get_slot("kpi")
        with open('./lookup/New_KPI.txt', 'r', encoding='utf8') as f:
            data = f.read()
            new_kpi_list = data.split('\n')

        if kpi in PREDEFINED_KPI:
            return [SlotSet("predefined", True), SlotSet("userdefined", False)]
        elif kpi in new_kpi_list:
            return [SlotSet("predefined", False), SlotSet("userdefined", True)]
        else:
            return [SlotSet("predefined", False), SlotSet("userdefined", False)]

class ActionNotFoundStatistics(Action):

    def name(self) -> Text:
        return "action_not_found_statistics"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Sorry, there is missing knowledge. Can you help me with it?",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])
        return []

class ActionNotFoundUserdefined(Action):

    def name(self) -> Text:
        return "action_not_found_userdefined"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Sorry, I did not find information about this KPI in knowledgebase. Do you want to define it as a new KPI?",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])
        return []

class ActionMapArgs(Action):

    def name(self) -> Text:
        return "action_map_args"

    def run(self, dispatcher, tracker, domain):
        arg_1 = tracker.get_slot("arg_1")
        arg_2 = tracker.get_slot("arg_2")
        arg_3 = tracker.get_slot("arg_3")
        args_dict = tracker.get_slot("args_dict")
        args_to_be_asked = tracker.get_slot("args_to_be_asked")

        if arg_1:
            args_dict[f"{args_to_be_asked[0]}"] = arg_1 
        if arg_2:
            args_dict[f"{args_to_be_asked[1]}"] = arg_2
        if arg_3:
            args_dict[f"{args_to_be_asked[2]}"] = arg_3 

        return [SlotSet("args_dict", args_dict)]

class ActionStoreKnowledge(Action):

    def name(self) -> Text:
        return "action_store_knowledge"

    def run(self, dispatcher, tracker, domain):
        args_dict = tracker.get_slot("args_dict")
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        current_place = tracker.get_slot("place")
        current_time = tracker.get_slot("time")
        
        try:
            # time mapping
            map_time = CheckTime()
            current_time = map_time.time_mapping(current_time[0], False)
            map_data_format = MapDataFormat()
            map_data_format.split_dict(args_dict, args_to_be_asked, place=current_place[0], time=current_time)
            # add new params
            map_data_format.add_new_params([])
            # add new geographic instances
            map_data_format.add_new_entries([])
            # response
            dispatcher.utter_message(text="Thank you! The knowledge is now in the knowledgebase😊")
        except Exception as e:
            print("action_store_knowledge:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)
        return []

class ActionStoreQuestions(Action):
    '''
    when the user presses 'deny' or inputs 'skip' and doesnt want to answer
    '''

    def name(self) -> Text:
        return "action_store_questions"

    def run(self, dispatcher, tracker, domain):

        data = []
        place = tracker.get_slot("place")
        time = tracker.get_slot("time")

        try:
            # user skip
            if tracker.get_slot("has_skip"):
                dispatcher.utter_message(text="Ok, I will add the question(s) into our Questionbase.")
                args_dict = tracker.get_slot("args_dict")

                for k,v in args_dict.items():
                    if v == 'skip':
                        data.append({"name": k, "place": place[0], "time": time[0]})
            # user deny
            else:
                dispatcher.utter_message(text="Ok, I will label the questions as unanswered and put them into Questionbase.")
                args_to_be_asked = tracker.get_slot("args_to_be_asked")

                
                for arg in args_to_be_asked:
                    data.append({"name": arg, "place": place[0], "time": time[0]})

            make_query = QueryMethods()
            make_query.insert_docu("Questionbase", data)
        except Exception as e:
            print("action_store_questions:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)

        return []

class ActionCheckSkip(Action):
    '''
    check if user skips some questions and predicts action accordingly.
    '''

    def name(self) -> Text:
        return "action_check_skip"

    def run(self, dispatcher, tracker, domain):
        args_dict = tracker.get_slot("args_dict")
        for k,v in args_dict.items():
            if v == 'skip':
                return [SlotSet("has_skip", True)]
        return [SlotSet("has_skip", False)]

class ActionAskAnotherQuiz(Action):
    '''
    check if user skips some questions and predicts action accordingly.
    '''

    def name(self) -> Text:
        return "action_ask_another_quiz"

    def run(self, dispatcher, tracker, domain):

        # ask user whether to have another quiz question
        dispatcher.utter_message(text="Would you like to have another quiz? 🤓",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])

        return []
        
# ------------------------------------------------------
# Below are the actions of nearby search
# ------------------------------------------------------
class AskForSlotAction(Action):
    def name(self) -> Text:
        return "action_ask_address"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text=f"What is the address of center of the search area?")
        return []

class AskForSlotAction(Action):
    def name(self) -> Text:
        return "action_ask_radius"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text=f"How many meters should the search area's radius be?")
        return []

class ActionNearbySearchStart(Action):
    '''
    tell user the search takes time
    '''
    def name(self) -> Text:
        return "action_nearby_search_start"
    
    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text="Your query is in process...This might take a few seconds.")

        return []

class ActionNearbySearch(Action):
    '''
    perform a nearby search
    '''

    def name(self) -> Text:
        return "action_nearby_search"

    def run(self, dispatcher, tracker, domain):
        address = tracker.get_slot("address")
        radius = tracker.get_slot("radius")
        try:
            print(address)
            print(radius)
            my_search = NearbySearch(5000, address)
            found_nodes, num_found_nodes = my_search.radius_search(radius)
            print(found_nodes)
            chargers_img_path = my_search.display_map(found_nodes)
            results = ""
            if found_nodes:
                for i in range(len(found_nodes)):
                    results += f"{i+1}. {found_nodes[i]['addr']}({round(found_nodes[i]['dist'], 2)}km)  \n"
                dispatcher.utter_message(text=f"In total, {num_found_nodes} charging stations were found within {radius} meters:  \n"+results)
                # dispatcher.utter_message(text="./my_map.html")
                dispatcher.utter_message(image=f"./actions/{chargers_img_path}")

            else:
                dispatcher.utter_message(text="No charging stations were found given the address and radius.")
        except Exception as e:
            print(e)
            dispatcher.utter_message(text=f"Sorry, an issue occurred. Our service is based on OpenStreetMap and this means there might be too many people accessing information from it right now. Please try again later or choose a different place/radius.")

        return []

class ActionResetRadius(Action):
    def name(self) -> Text:
        return "action_reset_radius"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        return [SlotSet("radius", None)]

# class ActionNearestSearch(Action):
#     '''
#     perform a nearest search
#     '''

#     def name(self) -> Text:
#         return "action_nearest_search"

#     def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="Your query is in process...This might take a few seconds.")
#         address = tracker.latest_message['address']
#         radius_list = [500, 1000, 3000, 5000]
#         try:
#             for radius in radius_list:
#                 my_search = NearbySearch(6000, address)
#                 found_nodes, num_found_nodes = my_search.radius_search(radius)
#                 if found_nodes:
#                     dispatcher.utter_message(text=f"The nearest charging station is {found_nodes[0]}, which is {found_nodes[1]} meters away.")
#                     break
#             if not found_nodes:
#                 dispatcher.utter_message(text="There are no charging stations found within radius of 5 km.")
#         except:
#             dispatcher.utter_message(text=f"Sorry, an issue occurred. Please try again later.")

#         return []

# ------------------------------------------------------
# Below are the actions for custom slot mapping(not used now)
# ------------------------------------------------------

class ActionCustomSlotMapping(Action):
    def name(self) -> Text:
        return "action_custom_slot_mapping"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        times = tracker.get_latest_entity_values("time")
        places = tracker.get_latest_entity_values("place")
        cardinals = tracker.get_latest_entity_values("cardinal")

        slotset = []

        slot_time = [time.value() for time in times]
        if len(slot_time) > 1:
            slotset.append([SlotSet("time", slot_time)])
        slot_place = [place.value() for place in places]
        if len(slot_place) > 1:
            slotset.append([SlotSet("place", slot_place)])
        slot_cardinal = [cardinal.value() for cardinal in cardinals]
        if len(slot_cardinal) > 1:
            slotset.append([SlotSet("cardinal", slot_place)])

        return slotset

# ------------------------------------------------------
# Below are the actions for 'add faqs'
# ------------------------------------------------------        
class AskForSlotAction(Action):
    def name(self) -> Text:
        return "action_ask_faqs_q"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text=f"What is the question you want to add to the FAQs?")
        return []

class AskForSlotAction(Action): 

    def name(self) -> Text:
        return "action_ask_faqs_a"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(text=f"What is the answer?")
        return []

class ActionAddFAQsFinished(Action):
    def name(self) -> Text:
        return "action_add_faqs_finished"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # add it to mongodb 
        # collection -> 'FAQs'
        faqs_q = tracker.get_slot("faqs_q")
        faqs_a = tracker.get_slot("faqs_a")

        try:
            # save it in mongodb
            make_query = QueryMethods()
            client = make_query.set_mongodb_connect()
            db = client['emobility']
            faqs = db['FAQs']
            faqs.insert_one({"question": faqs_q, "answer": faqs_a})
            dispatcher.utter_message(text="New FAQ added! Your FAQ will now be presented to other users 😄")

        except Exception as e:
            dispatcher.utter_message(text=SORRY_MESSAGE)

        return [SlotSet("identifier_faqs", None), SlotSet("faqs_a", None), SlotSet("faqs_q", None)]

# ------------------------------------------------------
# Below are the actions for 'emobility faqs'
# ------------------------------------------------------  
class ActionGiveFAQsFinished(Action):
    def name(self) -> Text:
        return "action_give_faqs_finished"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        query = tracker.latest_message['text']

        try:
            found_answer = start_retrieve.look_up(query)

            if found_answer:
                dispatcher.utter_message(text=found_answer)
            else:
                dispatcher.utter_message(text="Sorry but I don't have a answer for it.")

        except Exception as e:
            print("action_give_faqs_finished:",e)
            dispatcher.utter_message(text=SORRY_MESSAGE)

        return []        

        # try:
        #     make_query = QueryMethods()
        #     # get one random document from FAQs
        #     result = make_query.random_access("FAQs")
        #     dispatcher.utter_message(text=f"Q: {result['question']}  \n A: {result['answer']}")

        # except Exception as e:
        #     print("action_give_faqs_finished:",e)
        #     dispatcher.utter_message(text=SORRY_MESSAGE)

        # return []

# ------------------------------------------------------
# Query type classification
# ------------------------------------------------------  

class ActionQueryClassification(Action):
    # always be triggered after action 'nlu_fallback'
    def name(self) -> Text:
        return "action_query_classification"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # # prepare the fine-tuned BERT model
        # model = BertForSequenceClassification.from_pretrained(PATH)
        # # load tokenizer
        # tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
        # # get latest user message
        # user_text = tracker.latest_message['text']
        # # output query type prediction
        # predicted_type = predict(model, user_text, tokenizer)
        # # save prediction in a slot
        # if predicted_type:
        #     return[SlotSet("q_type", predicted_type)]
        text = tracker.latest_message['text']


        yes_or_no_words = ['was', 'is', 'do', 'does', 'did', 'are', 'were', 'will', 'would']
        ask_number_words = ['what', 'how many']
        ask_place_words = ['which', 'where']
        if text.split()[0].lower() in yes_or_no_words:
            return [SlotSet("q_type", "ask-yes-or-no"), SlotSet("query", text)]
        elif text.split()[0].lower() in ask_number_words:
            return [SlotSet("q_type", "ask-number"), SlotSet("query", text)]
        elif text.split()[0].lower() in ask_number_words:
            return [SlotSet("q_type", "ask-place"), SlotSet("query", text)]
        else:
            return [SlotSet("q_type", "ask-number"), SlotSet("query", text)]

        
        # if text.split()[0].lower() in yes_or_no_words:
        #     return [SlotSet("q_type", "ask-yes-or-no")]
        # elif "state" in text or "count" in text:
        #     if text.split()[0].lower() in ask_number_words:
        #         return [SlotSet("q_type", "ask-number")]
        #     else:
        #         return [SlotSet("q_type", "ask-place")]
        # elif "operator" in text or "provider" in text:
        #     return [SlotSet("q_type", "ask-provider")]
        # else:
        #     return [SlotSet("q_type", "ask-number")]

# ------------------------------------------------------
# restart
# ------------------------------------------------------  

class ActionRestarted(Action):

    def name(self):
        return "action_restart"

    def run(self, dispatcher, tracker, domain):
            return [Restarted()]
