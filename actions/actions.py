# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

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

from query_translator import QueryTranslator
from db import Querymethods
from process_newKPI import ResolveKPIDefinition
# from New_KPI import new_kpi_list
from bson import BSON
from bson.objectid import ObjectId
from nearby_search import NearbySearch


from rapidfuzz import process, fuzz
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity

REQUESTED_SLOT = "requested_slot"
PATH = "./actions/Query_classification/bert_model"
SORRY_MESSAGE = "I'm very sorry but something went wrong😵‍💫​ Our team will take care of this issue soon🔧 Thanks for your patience!"
SORRY_MESSAGE_GER = "Es tut mir leid, es scheint etwas schief gelaufen zu sein😵‍💫​ Unser Team wird dieses Problem bald lösen🔧 Vielen dank für die Geduld!"

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
        if user_input in ('0','1','2','3','4','5','6','7','8'):
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
            elif user_input == '5':
                return [SlotSet("service", 5)]
            elif user_input == '6':
                return [SlotSet("service", 6)]
            elif user_input == '7':
                return [SlotSet("service", 7)]
            elif user_input == '8':
                return [SlotSet("service", 8)]

        # user chooses by inputting the query
        user_intent = tracker.latest_message['intent'].get('name')
        if user_intent in ("agg_query", "group_sort_query", "filter_query", "limit_query", "charger_type", "charger_operator"):
            return [SlotSet("service", 1)]
        elif user_intent == ("nearby_search" or "nearest search"):
            return [SlotSet("service", 2)]
        elif user_intent == "start_define_kpi":
            return [SlotSet("service", 5)]
        elif user_intent == "quiz":
            return [SlotSet("service", 6)]
        elif user_intent == "main_menu":
            return [SlotSet("service", 0)]

        
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
        with open('/app/actions/lookup/GPE_Germany.txt', 'r', encoding='utf8') as f:
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

        if len(slot_value) == 1:
            if slot_value[0] in self.places_db():
                # validation succeeded, set the value of the "cuisine" slot to value
                return {"place": slot_value}
            else:
                # validation failed, set this slot to None so that the
                # user will be asked for the slot again
                if tracker.get_slot('lanaugage') == 'german':
                    dispatcher.utter_message(text="Oops, dieser Ort konnte nicht gefunden werden. Bitte geben Sie den offiziellen deutschen Namen des Ortes ein. Der Ort sollte ein Bundesland oder Landkreis in Deutschland sein. Es kann auch ein allgemeinerer Begriff wie 'Bundesland' oder 'Deutschland' verwendet werden.")
                else:
                    dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                return {"place": None}
        else:
            if slot_value[0] in self.places_db():
                if slot_value[1] in self.places_db():                    
                     return {"place": slot_value}
                else:
                    if tracker.get_slot('language') == 'german':
                        dispatcher.utter_message(text="Oops, dieser Ort konnte nicht gefunden werden. Bitte geben Sie den offiziellen deutschen Namen des Ortes ein. Der Ort sollte ein Bundesland oder Landkreis in Deutschland sein. Es kann auch ein allgemeinerer Begriff wie 'Bundesland' oder 'Deutschland' verwendet werden.")
                    else:
                        dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                    return {"place": None}                    
            else:
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(text="Oops, dieser Ort konnte nicht gefunden werden. Bitte geben Sie den offiziellen deutschen Namen des Ortes ein. Der Ort sollte ein Bundesland oder Landkreis in Deutschland sein. Es kann auch ein allgemeinerer Begriff wie 'Bundesland' oder 'Deutschland' verwendet werden.")
                else:
                    dispatcher.utter_message(text="Oops, this place was not found. Please enter a vaild place name by using its official name in German. The place should be a federal state(e.g. Baden-Württemberg) or county(e.g. Dresden) within Germany. Or you can enter general name like 'county' or 'federal state' or 'Germany'.")
                return {"place": None}

    def validate_DATE(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate time value."""

        for v in slot_value:
            check_time = CheckTime()
            mapped_time = check_time.time_mapping(v, False)

            if check_time.time_out_of_range(mapped_time):
                # time is out-of-range
                # user will be asked for the slot again
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(text = "Oops, es wurde ein invalider Zeitpunkt eigegeben oder der Zeitpunkt ist ausserhalb der Reichweite.")
                else:
                    dispatcher.utter_message(text="Oops, you have inputted an invalid time or your wished time is out of range.")
                return {"DATE": None}
            else:
                continue
        
        return {"DATE": slot_value}

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
        # updated_slots = domain_slots.copy()
        # updated_slots = required_slots
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
        DATE = tracker.get_slot("DATE")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Was ist die {args_to_be_asked[0]} in {place[0]} {'im' if DATE[0] != 'heute' else ''} {DATE[0]}? Geben Sie die Zahl in dem Format '123' für ganze Zahlen oder '123.45' für Kommazahlen ein. Falls Sie die Antwort nicht kennen oder die Frage nicht beantworten wollen, geben Sie 'skip' ein.")
        else:
            dispatcher.utter_message(text=f"What is the {args_to_be_asked[0]} of {place[0]} {'in' if DATE[0] != 'now' else ''} {DATE[0]}? Enter the number using the format '123' for integer or '123.45' for decimal. If you don't know or don't want to answer it, please type 'skip'.")
        return []

class AskForARG2(Action):
    def name(self) -> Text:
        return "action_ask_arg_2"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        place = tracker.get_slot("place")
        DATE = tracker.get_slot("DATE")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Was ist die {args_to_be_asked[1]} in {place[0]} {'im' if DATE[0] != 'heute' else ''} {DATE[0]}? Geben Sie die Zahl in dem Format '123' für ganze Zahlen oder '123.45' für Kommazahlen ein. Falls Sie die Antwort nicht kennen oder die Frage nicht beantworten wollen, geben Sie 'skip' ein.")
        else:
            dispatcher.utter_message(text=f"What is the {args_to_be_asked[1]} of {place[0]} {'in' if DATE[0] != 'now' else ''} {DATE[0]}? If you don't know or don't want to answer it, please type 'skip'.")
        return []

class AskForARG3(Action):
    def name(self) -> Text:
        return "action_ask_arg_3"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        args_to_be_asked = tracker.get_slot("args_to_be_asked")
        place = tracker.get_slot("place")
        DATE = tracker.get_slot("DATE")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Was ist die {args_to_be_asked[0]} in {place[0]} {'im' if DATE[0] != 'heute' else ''} {DATE[0]}? Geben Sie die Zahl in dem Format '123' für ganze Zahlen oder '123.45' für Kommazahlen ein. Falls Sie die Antwort nicht kennen oder die Frage nicht beantworten wollen, geben Sie 'skip' ein.")
        else:
            dispatcher.utter_message(text=f"What is the {args_to_be_asked[2]} of {place[0]} {'in' if DATE[0] != 'now' else ''} {DATE[0]}? If you don't know or don't want to answer it, please type 'skip'.")
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

        if tracker.get_slot('language') == 'german':
            if intent == 'charger_type':
                buttons = [
                {"title": "Schnell Ladestationen","payload": ['/inform{{"kpi":"Charging stations"}}, /inform{{"charger_type":"fast"}}']},
                {"title": "Normal Ladestationen", "payload": ['/inform{{"kpi":"Charging stations"}}, /inform{{"charger_type":"normal"}}']},        
                ]
            elif intent == 'charger_operator':
                buttons = [
                {"title": "Ladestationen Betreiber", "payload": '/inform{{"operator":"operator"}}'},
                ]
            else:
                buttons = [
                {"title": "Standort","payload": '/inform{{"kpi":"Locations"}}'},
                {"title": "Ladestationen", "payload": '/inform{{"kpi":"Charging stations"}}'},
                {'title':"Ladepunkte", "payload": '/inform{{"kpi":"Charging points"}}'},
                {"title": "Pkw pro Ladepunkt","payload": '/inform{{"kpi":"Cars_per_charging_point"}}'},
                {"title": "Ladepunkte pro 1,000 Pkw", "payload": '/inform{{"kpi":"Charging_points_per_1,000_cars"}}'},
                {'title':"Zielerreichung", "payload": '/inform{{"kpi":"Percentage_of_target"}}'},        
                ]
            dispatcher.utter_message(text=f"An welchem KPI haben Sie interesse? Wählen Sie einen der vordefiniteren KPIs oder geben sie einen Benutzerdefinierten oder einen neuen KPI ein. Bitte geben Sie auch den JPI noch einmal ein, wenn er bereits in der Anfrage enthalten war.")
        else:
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
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Der Ort ist {place}  \nZeitpunkt ist {DATE}  \nkpi ist {kpi}")
        else:
            dispatcher.utter_message(text=f"place is {place}  \ntime is {DATE}  \nkpi is {kpi}")
        return []

# class ActionResetSlots(Action):

#     def name(self) -> Text:
#         return "action_reset_slots"

#     def run(self, dispatcher, tracker, domain):
#         # return [SlotSet("place", None), SlotSet("kpi", None), SlotSet("DATE", None), SlotSet("mapped_time", None), 
#         # SlotSet("max", None), SlotSet("min", None), SlotSet("avg", None), SlotSet("desc", None),
#         # SlotSet("asc", None), SlotSet("le", None), SlotSet("ge", None), SlotSet("bet", None), SlotSet("CARDINAL", None)]
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
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Ort: {place} \nkpi: {kpi} \nZeitpunkt:{DATE}")
        else:
            dispatcher.utter_message(text=f"place: {place} \nkpi: {kpi} \ntime:{DATE}")

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
        DATE = tracker.get_slot("DATE")
        kpi = tracker.get_slot("kpi")
        operator = tracker.get_slot("operator")
        charger_type = tracker.get_slot("charger_type")
        if tracker.get_slot('language') == 'german':
            if charger_type:
                dispatcher.utter_message(text=f"Ort: {place[0] if len(place)==1 else place}  \nkpi: {charger_type} {kpi}",
                buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
                ])
            elif operator:
                dispatcher.utter_message(text=f"Ort: {place[0] if len(place)==1 else place}  \nkpi: Ladestationen Betreiber",
                buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
                ])
            else:
                dispatcher.utter_message(text=f"Ort: {place[0] if len(place)==1 else place}  \nkpi: {kpi}  \nZeitpunkt: {DATE[0] if len(DATE)==1 else DATE}",
                buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
                ])
        else:
            if charger_type:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {charger_type} {kpi}",
                buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
                ])
            elif operator:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: Charging_station_operators",
                buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
                ])
            else:
                dispatcher.utter_message(text=f"place: {place[0] if len(place)==1 else place}  \nkpi: {kpi}  \ntime: {DATE[0] if len(DATE)==1 else DATE}",
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
        options_mapping = {
            1: 'continue asking',
            2: 'search again',
            5: 'add another KPI',
            6: 'add another knowledge',
            7: 'add another FAQ',
            4: 'have another FAQ'
        }
        options_mapping_ger = {
            1: "weiter fragen",
            2: 'erneut suchen',
            5: 'einen weiteren KPI hinzufügen',
            6: 'weiteres Wissen hinzufügen',
            7: 'ein weiteres FAQ hinzufügen',
            4: 'ein weiteres FAQ haben'
        }
        if service in (1,2,4,5,6,7):
            if tracker.get_slot('language') == 'german':

                dispatcher.utter_message(text=f"Möchten Sie...?",
                buttons= [
                    {"title": f"{options_mapping_ger[service] if service else 'diesen Dienst weiterführen'}","payload": "/continue"},
                    {"title": "zurück zum Hauptmenü", "payload": "/main_menu"}
                ])
            else:
                dispatcher.utter_message(text=f"Do you want to...?",
                buttons= [
                    {"title": f"{options_mapping[service] if service else 'continue this service'}","payload": "/continue"},                
                    {"title": "back to main menu", "payload": "/main_menu"}
                ])
        elif service in (3,8):
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=f"Möchten Sie...?",
                    buttons= [
                    {"title": "zurück zum Hauptmenü", "payload": "/main_menu"}
                ])
            else:
                dispatcher.utter_message(text=f"Do you want to...?",
                    buttons= [
                    {"title": "back to main menu", "payload": "/main_menu"}
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
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text="Vordefinierte KPIs:  \n Standorte  \n Ladestationen  \n Ladepunkte  \n Pkw pro Ladepunkt  \n Ladepunkte pro 1,000 Pkw  \n Zielerreichung  \n Schnell Ladestationen  \n Normal Ladestationen  \n Ladestationen Betreiber")


            with open('/app/actions/lookup/New_KPI.txt', 'r', encoding='utf8') as f:
                data = f.read()
                new_kpi_list = data.split('\n')
            
            if new_kpi_list is None:
                kpi_str = "(leer)"

            else:
                kpi_str = "Benutzerdefinierte KPIs:  \n "
                for kpi in new_kpi_list:
                    kpi_str += f"{kpi}  \n "

            dispatcher.utter_message(text=kpi_str)   
            hints = "Sie können nun anfangen mir Fragen zu stellen. Folgen Sie einfach dem folgenden Beispiel:  \n Für vordefinierte KPI:  \n 1.Was ist die Anzal der Ladestationen in Berlin im Juli 2022?  \n 2.Welches Bundesland hat die höchste Zielerreichung im März 2021?  \n 3.Was ist der Anstieg der Pkw pro Ladepunkt in Bayern vom 01.2022 bis zum 05.2022?  \n Für Benutzerdefinierte KPI:  \n Was ist charging_points_per_person in Deutschland im August 2022?  \n Es stehen viele weitere Fragen zur Auswahl. Probieren Sie es einfach aus.😄. "

        else:
            dispatcher.utter_message(text="Predefined KPIs:  \n Locations  \n Charging_stations  \n Charging_points  \n Cars_per_charging_point  \n Charging_points_per_1,000_cars  \n Percentage_of_target  \n fast Charging_stations  \n normal Charging_stations  \n Charging_station_operators")

            with open('/app/actions/lookup/New_KPI.txt', 'r', encoding='utf8') as f:
                data = f.read()
                new_kpi_list = data.split('\n')
            
            if new_kpi_list is None:
                kpi_str = "(empty)"

            else:
                kpi_str = "Userdefined KPIs:  \n "
                for kpi in new_kpi_list:
                    kpi_str += f"{kpi}  \n "

            dispatcher.utter_message(text=kpi_str)        
            hints = "You can start asking me your query. Follow the examples below if you don't know how to ask properly:  \n For predefined KPI:  \n 1.What is the number of charging\_points in Berlin in July 2022?  \n 2.Which county had the highest Percentage\_of\_target in March 2021?  \n 3.What is the increased value of Cars\_per\_charging\_point in Bayern from 01.2022 to 05.2022?  \n For userdefined KPI:  \n What is charging_points_per_person in Germany in August 2022?  \n There are many more queries available. Explore and find them out😄 \n To let the chatbot understand you better, add '\_' between words for KPI names." 
        
        dispatcher.utter_message(text=hints)  
        return []

class ActionExecuteAggQuery(Action):
   def name(self) -> Text:
      return "action_execute_agg_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent agg_query.
        
        """

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        avg = tracker.get_slot("avg")
        increase = tracker.get_slot("increase")
        q_type = tracker.get_slot("q_type") 

        translator = QueryTranslator()
        if len(DATE) == 1:
            is_prediction = translator.kpi_is_prediction(DATE[0], False)
        else:
            is_prediction = False

        try:

            make_query = Querymethods()
            
            # mapped_kpi = predefined_kpi_mapping(PREDEFINED_KPI_MAPPING, kpi)

            if kpi in PREDEFINED_KPI:
                q = translator.agg_query(kpi, place, DATE, max=max, min=min, avg=avg, increase=increase)
                print("q ", q)
                if len(q) == 1:
                    results_1 = make_query.execute_sqlquery(q[0])
                    print('result_1 ', results_1)
                else:
                    # make_query.execute_sqlquery(q[0]) -> [(Decimal('6418.4646875688928426'), 'Bayern')]
                    results_1, results_2 = make_query.execute_sqlquery(q[0])[0], make_query.execute_sqlquery(q[1])[0]
                    print('result1 ', results_1)
                    print('result2 ', results_2)
                # agg_query has q_type 'ask-number' or 'ask-place'
                if tracker.get_slot('language') == 'german':
                    if q_type == "ask-number":
                        if not avg:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"Die Anzahl an {kpi} in {place[0]} {'' if DATE[0] == 'now' else 'im'} {DATE[0]} {'ist' if is_prediction or DATE[0] == 'now' else 'war' } "+str(round(results_1[0]))+ f"({round(100*results_1[0]/results_2[0], 2)}% des Gesamtanteils in Deutschland)"+"."
                                else:
                                    if len(DATE) != 1:
                                        # e.g. increase from 2019 to 2021
                                        text = f"Der Anstieg der {kpi} in {place[0]} vom {DATE[0]} bis zum {DATE[1]} war "+str(round(results_1[0][0]))+ "."
                                    else:
                                        # e.g. increase last year
                                        text = f"Der Anstieg der {kpi} in {place[0]} in {DATE[0]} war "+str(round(results_1[0][0]))+"."
                            else:
                                if not increase:
                                    text = f"Die {kpi} in {place[0]} {'' if DATE == 'now' else 'im'} {DATE[0]} {'ist' if is_prediction or DATE == 'now' else 'war' } "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."            
                                else:
                                    if len(DATE) != 1:
                                        text = f"Der Anstieg der {kpi} in {place[0]} vom {DATE[0]} bis zum {DATE[1]} war "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."        
                                    else:
                                        text = f"Der Anstieg der {kpi} in {place[0]} in {DATE[0]} war "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                        else:
                            if len(place) == 1:
                                if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                    if not increase:
                                        text = f"Die {avg} Anzahl an {kpi} in einem  {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} {'' if DATE[0] == 'now' else 'im'} {DATE[0]} {'ist' if is_prediction or DATE[0] == 'now' else 'war' } "+str(round(results_1[0]))+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"Der {avg} anstieg der {kpi} in einem {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} vom {DATE[0]} bis zum {DATE[1]} war "+str(round(results_1[0][0]))+"."
                                        else:
                                            text = f"Der {avg} anstieg der {kpi} in einem  {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} im  {DATE[0]} war "+str(round(results_1[0][0]))+"."
                                else:
                                    if not increase:
                                        text = f"Die {avg} Anzahl an{kpi} in einem  {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} {'' if DATE[0] == 'now' else 'im'} {DATE[0]} {'ist' if is_prediction or DATE[0] == 'now' else 'war' } "+str(round(results_1[0],1))+'%'+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"Der {avg} Anstieg der {kpi} in einem {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} {'' if DATE[0] == 'now' else ''} vom {DATE[0]} bis {DATE[1]} war "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                        else:
                                            text = f"Der {avg} Anstieg der {kpi} in einem  {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} {'' if DATE[0] == 'now' else 'im'} {DATE[0]} war "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                            else:
                                if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                    if not increase:
                                        text = f"Die {avg} Anzahl an {kpi} of {place[0]} in {place[1]} {'' if DATE[0] == 'now' else 'in'} in {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"Der {avg} Anstieg der {kpi} von {place[0]} in {place[1]} vom {DATE[0]} bis zum {DATE[1]} war "+str(round(results_1[0][0]))+"."
                                        else:
                                            text = f"Der {avg} Anstieg der {kpi} von {place[0]} in {place[1]} im {DATE[0]} war "+str(round(results_1[0][0]))+"."
                                else:
                                    if not increase:
                                        text = f"Die {avg} Anzahl an {kpi} von {place[0]} in {place[1]} {'' if DATE[0] == 'now' else 'im'} {DATE[0]} {'ist' if is_prediction or DATE[0] == 'now' else 'war' } "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"Der {avg} Anstieg der {kpi} von {place[0]} in {place[1]} vom {DATE[0]} bis zum {DATE[1]} war "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."   
                                        else:
                                            text = f"The {avg} Anstieg der {kpi} von {place[0]} in {place[1]} im {DATE[0]} war "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                    elif q_type == "ask-place":
                        if len(place) == 1:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"{results_1[1]} {'hat' if DATE[0] == 'now' else 'hatte'} die {max if max else ''}{min if min else ''} Anzahl an {kpi} {'' if DATE[0] == 'now' else 'im'} {DATE[0]}, welches  "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% des Gesamtanteils in Deutschland ist.)"+"."   
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[0][1]} hatte den {max if max else ''}{min if min else ''} Anstieg der {kpi} vom {DATE[0]} bis zum {DATE[1]}, mit "+str(round(results_1[0][0]))+"."              
                                    else:
                                        # results_1  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
                                        print("results_1 ", results_1)
                                        text = f"{results_1[0][1]} hatte den {max if max else ''}{min if min else ''} Anstieg der {kpi} im {DATE[0]}, mit "+str(round(results_1[0][0]))+"."
                            else:
                                if not increase:
                                    text = f"{results_1[1]} {'hat' if DATE[0] == 'now' else 'hatte'} die {max if max else ''}{min if min else ''} Anzahl an {kpi} {'' if DATE[0] == 'now' else 'im'} {DATE[0]}, mit "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} vom {DATE[0]} bis zum {DATE[1]}, mit "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"."
                                    else:
                                        text = f"{results_1[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} im {DATE[0]}, mit "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"." 
                        else:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"{results_1[1]} in {place[1]} {'hat' if DATE[0] == 'now' else 'hatte'} die {max if max else ''}{min if min else ''} Anzahl an {kpi} {'' if DATE[0] == 'now' else 'im'} {DATE[0]},mit  "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% des Gesamtanteils von Deutschland)"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} in {place[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} vom {DATE[0]} bis zum {DATE[1]},mit  "+str(round(results_1[0]))+"."
                                    else:
                                        text = f"{results_1[1]} in {place[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} im {DATE[0]}, mit "+str(round(results_1[0]))+"."
                            else:
                                if not increase:
                                    text = f"{results_1[1]} in {place[1]} {'hat' if DATE[0] == 'now' else 'hatte'} die {max if max else ''}{min if min else ''} Anzal von {kpi} {'' if DATE[0] == 'now' else 'im'} {DATE[0]},mit"+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} in {place[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} vom {DATE[0]} bis zum {DATE[1]},mit "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                    else:
                                        text = f"{results_1[1]} in {place[1]} hatte den {max if max else ''}{min if min else ''} Anstieg an {kpi} im {DATE[0]}, mit "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                    else:
                        # (not perfect)general template that handles wrong classification
                        text = f"{kpi}  is "+str(round(results_1[0]))                               

                else:
                    if q_type == "ask-number":
                        if not avg:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"The number of {kpi} in {place[0]} {'' if DATE[0] == 'now' else 'in'} {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({round(100*results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
                                else:
                                    if len(DATE) != 1:
                                        # e.g. increase from 2019 to 2021
                                        text = f"The increase of {kpi} in {place[0]} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0][0]))+ "."
                                    else:
                                        # e.g. increase last year
                                        text = f"The increase of {kpi} in {place[0]} in {DATE[0]} was "+str(round(results_1[0][0]))+"."
                            else:
                                if not increase:
                                    text = f"The {kpi} in {place[0]} {'' if DATE == 'now' else 'in'} in {DATE[0]} {'is' if is_prediction or DATE == 'now' else 'was' } "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."            
                                else:
                                    if len(DATE) != 1:
                                        text = f"The increase of {kpi} in {place[0]} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."        
                                    else:
                                        text = f"The increase of {kpi} in {place[0]} in {DATE[0]} was "+str(round(results_1[0][0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                        else:
                            if len(place) == 1:
                                if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                    if not increase:
                                        text = f"The {avg} number of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if DATE[0] == 'now' else 'in'} {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0][0]))+"."
                                        else:
                                            text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} at {DATE[0]} was "+str(round(results_1[0][0]))+"."
                                else:
                                    if not increase:
                                        text = f"The {avg} {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if DATE[0] == 'now' else 'in'} {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0],1))+'%'+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if DATE[0] == 'now' else 'in'} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                        else:
                                            text = f"The {avg} increase of {kpi} of a  {'state' if 'state' in place[0].lower() else 'county'} {'' if DATE[0] == 'now' else 'in'} {DATE[0]} was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                            else:
                                if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                    if not increase:
                                        text = f"The {avg} number of {kpi} of {place[0]} in {place[1]} {'' if DATE[0] == 'now' else 'in'} in {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0]))+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0][0]))+"."
                                        else:
                                            text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} in {DATE[0]} was "+str(round(results_1[0][0]))+"."
                                else:
                                    if not increase:
                                        text = f"The {avg} {kpi} of {place[0]} in {place[1]} {'' if DATE[0] == 'now' else 'in'} in {DATE[0]} {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                    else:
                                        if len(DATE) != 1:
                                            text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} from {DATE[0]} to {DATE[1]} was "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."   
                                        else:
                                            text = f"The {avg} increase of {kpi} of {place[0]} in {place[1]} in {DATE[0]} was "+str(round(results_1[0], 1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                    elif q_type == "ask-place":
                        if len(place) == 1:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"{results_1[1]} {'has' if DATE[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if DATE[0] == 'now' else 'in'} {DATE[0]}, which {'is' if is_prediction or DATE[0] == 'now' else 'was'} "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."   
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {DATE[0]} to {DATE[1]}, which was "+str(round(results_1[0][0]))+"."              
                                    else:
                                        # results_1  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
                                        print("results_1 ", results_1)
                                        text = f"{results_1[0][1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {DATE[0]}, which was "+str(round(results_1[0][0]))+"."
                            else:
                                if not increase:
                                    text = f"{results_1[1]} {'has' if DATE[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if DATE[0] == 'now' else 'in'} {DATE[0]}, which {'is' if is_prediction or DATE == 'now' else 'was'} "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {DATE[0]} to {DATE[1]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"."
                                    else:
                                        text = f"{results_1[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {DATE[0]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''} "+"." 
                        else:
                            if kpi in ('Locations', 'Charging_stations', 'Charging_points'):
                                if not increase:
                                    text = f"{results_1[1]} in {place[1]} {'has' if DATE[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} number of {kpi} {'' if DATE[0] == 'now' else 'in'} {DATE[0]}, which {'is' if is_prediction or DATE[0] == 'now' else 'was' } "+str(round(results_1[0]))+ f"({100*round(results_1[0]/results_2[0], 2)}% of the total in Germany)"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {DATE[0]} to {DATE[1]}, which was "+str(round(results_1[0]))+"."
                                    else:
                                        text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {DATE[0]}, which was "+str(round(results_1[0]))+"."
                            else:
                                if not increase:
                                    text = f"{results_1[1]} in {place[1]} {'has' if DATE[0] == 'now' else 'had'} the {max if max else ''}{min if min else ''} {kpi} {'' if DATE[0] == 'now' else 'in'} {DATE[0]}, which {'is' if is_prediction or DATE[0] == 'now' else 'was' }"+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                else:
                                    if len(DATE) != 1:
                                        text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} from {DATE[0]} to {DATE[1]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                                    else:
                                        text = f"{results_1[1]} in {place[1]} had the {max if max else ''}{min if min else ''} increase of {kpi} in {DATE[0]}, which was "+str(round(results_1[0],1))+f"{'%' if kpi == 'Percentage_of_target' else ''}"+"."
                    else:
                        # (not perfect)general template that handles wrong classification
                        text = f"{kpi}  is "+str(round(results_1[0]))                               


                dispatcher.utter_message(text=text)

                if is_prediction:
                    if tracker.get_slot('language') == 'german':
                        dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                    else:
                        dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is September 2022, so this is a prediction based on past values.")

            else:
                # start process user-defined KPI
                # look for KPI definition
                result = make_query.find_value("new_kpi_definition", "kpi_name", kpi, "kpi_definition")
                # dispatcher.utter_message(text=f"{result['kpi_definition']}")


                if result:
                    # defintion found
                    # extract parameters
                    kpi_definition = result["kpi_definition"]
                    resolve_KPI = ResolveKPIDefinition()
                    params = resolve_KPI.parameter_extraction(kpi_definition)

                    # fill arguments that are available in database
                    # return missing information
                    args_dict, args_to_be_asked = resolve_KPI.argument_filling(params, place, DATE)

                    print("definition found, args_to_be_asked ", args_to_be_asked)

                    # only set the slot args_to_be_asked when it's not empty
                    if args_to_be_asked:
                        return [SlotSet("self_learning", True), SlotSet("args_dict", args_dict), SlotSet("args_to_be_asked", args_to_be_asked), SlotSet("kpi_definition_not_form", kpi_definition)]
                    else:
                        return [SlotSet("self_learning", True), SlotSet("args_dict", args_dict), SlotSet("kpi_definition_not_form", kpi_definition)]
                else:
                    # no definition found
                    return [SlotSet("self_learning", True), FollowupAction("action_not_found_userdefined")]
        except Exception as e:
            print("action_agg_query:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)

class ActionContinueAggQuery(Action):

    def name(self) -> Text:
        return "action_continue_agg_query"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        kpi_definition_not_form = tracker.get_slot("kpi_definition_not_form")
        args_dict = tracker.get_slot("args_dict")
        #  methods from class ResolveKPIDefinition  
        try:   
            resolve_kpi = ResolveKPIDefinition()
            result = resolve_kpi.arithmetic(kpi_definition_not_form, args_dict)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=f"Der {kpi} in {place[0]} im {DATE[0]} ist {round(result) if round(result) >=1 else 'kleiner als 1'}")
            else:
                dispatcher.utter_message(text=f"The {kpi} in {place[0]} in {DATE[0]} is {round(result) if round(result) >=1 else 'less than 1'}")
        except Exception as e:
            print("action_continue_agg_query:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)
        return []

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
            make_query = Querymethods()
            translator = QueryTranslator()

            q = translator.charger_type_query(place, charger_type, max=max, min=min, avg=avg)
            print("q ", q)



            if len(q) == 1:
                results_1 = make_query.execute_sqlquery(q[0])
            else:
                results_1, results_2 = make_query.execute_sqlquery(q[0]), make_query.execute_sqlquery(q[1])
                print('result_1', results_1[0])
                print('result_2', results_2[0])

            if tracker.get_slot('language') == 'german':
                if q_type == "ask-number":
                    if not avg:
                        text = f"Die Anzal an {charger_type} {kpi} in {place[0]} ist "+str(round(results_1[0][0]))+ f"({round(100*results_1[0][0]/results_2[0][0], 2)}% der Gesamtanzahl der {charger_type} Ladestationen in Deutschland)"+"."
                    else:
                        if len(place) == 1:
                            text = f"Die {avg} Anzahl an {charger_type} {kpi} in einem {'Bundesland' if 'bundesland' in place[0].lower() else 'Landkreis'} ist "+str(round(results_1[0][0]))+"."
                        else:
                            text = f"DIe {avg} Anzahl an {charger_type} {kpi} von {place[0]} in {place[1]} ist "+str(round(results_1[0][0]))+"."
                elif q_type == "ask-place":
                    if len(place) == 1:
                        text = f"{results_1[0][0]} hat die {max if max else ''}{min if min else ''} Anzahl an {charger_type} {kpi}, mit "+str(round(results_1[0][1]))+ f"({100*round(results_1[0][1]/results_2[0][0], 2)}% des Gesamtanteils der {charger_type} Ladestationen in Deutschland)"+"."   
                    else:
                        text = f"{results_1[0][1]} in {place[1]} hat die {max if max else ''}{min if min else ''} Anzahl an {charger_type} {kpi}, mit "+str(round(results_1[0][0]))+ f"({round(results_1[0][0]/results_2[0][0], 2)}% des Gesamtanteils der {charger_type} Ladestationen in Deutschland)"+"."

                else:           
                    text = f"{kpi} ist "+str(round(results_1[0][0]))
            else:
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
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
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
            make_query = Querymethods()
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
            if tracker.get_slot('language') == 'german':
                if q_type == "ask-provider":
                    if max or min:
                        text = f"Der {'särkste' if max else 'schwächste'} Anbieter in {place[0]} ist {results_1[0]} mit {results_1[1]} ({100*round(results_1[1]/results_2[0], 2)}% des Gesamtanteils in Deutschland)" 
                    else:
                        length_results = len(results_1)
                        if length_results > 20:
                            text = f"Es giebt {len(results_1)} Betreiber in {place[0]}, hier sind die top 20:  \n"
                            for result in results_1[:20]:
                                text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}%)  \n"
                        else:
                            text = f"Es giebt {len(results_1)} Betreiber in {place[0]}:  \n"
                            for result in results_1:
                                text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}%)  \n"                

                        text += "*Die Zahl zeigt die Anzahl an Ladestationen die von jedem Betreiber betrieben werden, in Klammern ist die Anzahl des Gesamtanteils in Deutschland."                   
                        dispatcher.utter_message(text=text)
                else:           
                    for result in results_1:
                        print("results_2", results_2)
                        text += f"{result[0]}, {round(result[1])}({100*round(result[1]/results_2[0][0], 2)}% des Gesamtanteils in Deutschland)  \n"
            else:
                if q_type == "ask-provider":
                    if max or min:
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
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)
        return []



class ActionExecuteGroupSortQuery(Action):
   def name(self) -> Text:
      return "action_execute_group_sort_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent group_sort_query
        
        """

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        desc = tracker.get_slot("desc")
        asc = tracker.get_slot("asc")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        q_type = tracker.get_slot("q_type") 
        increase = tracker.get_slot("increase")

        try:
            translator = QueryTranslator()
            make_query = Querymethods()
            if len(DATE) == 1:
                is_prediction = translator.kpi_is_prediction(DATE[0], False)
            else:
                is_prediction = False
    
            q = translator.group_sort_query(kpi, DATE, desc=desc, asc=asc, max=max, min=min, increase=increase)

            results = make_query.execute_sqlquery(q[0])
            res =""

            if q_type == "ask-place":
                if results:
                    for result in results:
                        res += f"{result[1]}, {round(result[0]) if kpi != 'Percentage of target' else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                    dispatcher.utter_message(text=res)

                    if is_prediction:
                        if tracker.get_slot('language') == 'german':
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                        else:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")

                else:
                    if tracker.get_slot('language') == 'german':
                        dispatcher.utter_message(text='Für diese Frage wurde kein Ergebniss gefunden')
                    else:
                        dispatcher.utter_message(text="No results found for your query.")
            
            else:
                # now group_sort_query only has one q_type 'ask-place', so this branch has the same content
                # for future modification reserved
                if results:
                    for result in results:
                        res += f"{result[1]}, {round(result[0]) if kpi != 'Percentage_of_target' else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                    dispatcher.utter_message(text=res)

                    if is_prediction:
                        if tracker.get_slot('language') == 'german':
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                        else:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")

                else:
                    dispatcher.utter_message(text="No results found for your query.")
        except Exception as e:
            print("action_execute_group_sort_query:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)
 
        return []

class ActionExecuteFilterQuery(Action):
   def name(self) -> Text:
      return "action_execute_filter_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs after intent filter_query
        
        """

        place = tracker.get_slot("place")
        kpi = tracker.get_slot("kpi")
        DATE = tracker.get_slot("DATE")
        CARDINAL = tracker.get_slot("CARDINAL")
        ge = tracker.get_slot("ge")
        le = tracker.get_slot("le")
        bet = tracker.get_slot("bet")
        q_type = tracker.get_slot("q_type") 
        user_input = tracker.latest_message['text']
        try:
            translator = QueryTranslator()
            make_query = Querymethods()
            if len(DATE) == 1:
                is_prediction = translator.kpi_is_prediction(DATE[0], False)
            else:
                is_prediction = False
            increase = tracker.get_slot("increase")
            q = translator.filter_query(kpi, place, DATE, ge=ge, le=le, bet=bet, CARDINAL=CARDINAL, increase=increase)
            print('filter q: ', q)
            results = make_query.execute_sqlquery(q[0])
            text =""
            if tracker.get_slot('language') == 'german':
                if q_type == "ask-place":

                    if len(results) <= 20:
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    else:
                        text += f"Insgesamt gab es {len(results)} Ergebnisse. Hier sind die ersten 20 Ergebnisse:  \n"
                        results = results[:20]
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    if text == "":
                        dispatcher.utter_message(text="Es wurde kein Ergebniss für ihre Frage gefunden.")
                    else:
                        dispatcher.utter_message(text=text)
                        if is_prediction:
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")

                elif q_type == "ask-yes-or-no":
                    if len(results) == 1:
                        if kpi != "Percentage_of_target":
                            if not increase:
                                if ge:
                                    text = f"{'Ja' if results[1] > CARDINAL else 'Nein'}, die Anzahl der {kpi} war {'' if results[1] > CARDINAL else 'nicht'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Ja' if results[1] < CARDINAL else 'Nein'}, die Anzahl der {kpi} war {'' if results[1] < CARDINAL else 'nicht'} {le} {CARDINAL}."
                            else:
                                if ge:
                                    text = f"{'Ja' if results[1] > CARDINAL else 'Nein'}, Der Anstieg an {kpi} war {'' if results[1] > CARDINAL else 'nicht'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Ja' if results[1] < CARDINAL else 'Nein'}, Der Anstieg an {kpi} war {'' if results[1] < CARDINAL else 'nicht'} {le} {CARDINAL}."            
                        else:
                            if not increase:
                                if ge:
                                    text = f"{'Ja' if results[0] > CARDINAL else 'Nein'}, die Anzal der {kpi} war {'' if results[0] > CARDINAL else 'nicht'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Ja' if results[0] < CARDINAL else 'Nein'}, die Anahld der {kpi} war {'' if results[0] < CARDINAL else 'nicht'} {le} {CARDINAL}."
                            else:
                                if ge:
                                    text = f"{'Ja' if results[0] > CARDINAL else 'Nein'}, der Anstieg an der {kpi} war {'' if results[0] > CARDINAL else 'nicht'} {ge} {CARDINAL}%."
                                else: 
                                    text = f"{'Ja' if results[0] < CARDINAL else 'Nein'}, der Anstieg an der {kpi} war {'' if results[0] < CARDINAL else 'nicht'} {le} {CARDINAL}%."         
                        if text == "":
                            dispatcher.utter_message(text="Es wurde kein Ergebniss für Ihre Frage gefunden.")
                        else:
                            dispatcher.utter_message(text=text)
                            if is_prediction:
                                dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                    else:
                        dispatcher.utter_message(text="Nur einzeilige Ergebnisse werden für Ja und Nein Fragen akzeptiert.")
                
                else:
                    if len(results) <= 20:
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    else:
                        text += f"Insgesamt gab es {len(results)} Ergebnisse. Hier sind die ersten 20 Ergebnisse:  \n"
                        results = results[:20]
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    if text == "":
                        dispatcher.utter_message(text="Es wurden keine Ergebnisse für ihre Frage gefunden.")
                    else:
                        dispatcher.utter_message(text=text)
                        if is_prediction:
                            
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
            else:
                if q_type == "ask-place":

                    if len(results) <= 20:
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    else:
                        text += f"In total {len(results)} returned. Here are the first 20 results:  \n"
                        results = results[:20]
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    if text == "":
                        dispatcher.utter_message(text="No results found for your query.")
                    else:
                        dispatcher.utter_message(text=text)
                        if is_prediction:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")

                elif q_type == "ask-yes-or-no":
                    if len(results) == 1:
                        if kpi != "Percentage_of_target":
                            if not increase:
                                if ge:
                                    text = f"{'Yes' if results[1] > CARDINAL else 'No'}, the number of {kpi} was {'' if results[1] > CARDINAL else 'not'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Yes' if results[1] < CARDINAL else 'No'}, the number of {kpi} was {'' if results[1] < CARDINAL else 'not'} {le} {CARDINAL}."
                            else:
                                if ge:
                                    text = f"{'Yes' if results[1] > CARDINAL else 'No'}, the increase of {kpi} was {'' if results[1] > CARDINAL else 'not'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Yes' if results[1] < CARDINAL else 'No'}, the increase of {kpi} was {'' if results[1] < CARDINAL else 'not'} {le} {CARDINAL}."            
                        else:
                            if not increase:
                                if ge:
                                    text = f"{'Yes' if results[0] > CARDINAL else 'No'}, the {kpi} was {'' if results[0] > CARDINAL else 'not'} {ge} {CARDINAL}."
                                else: 
                                    text = f"{'Yes' if results[0] < CARDINAL else 'No'}, the {kpi} was {'' if results[0] < CARDINAL else 'not'} {le} {CARDINAL}."
                            else:
                                if ge:
                                    text = f"{'Yes' if results[0] > CARDINAL else 'No'}, the increase of {kpi} was {'' if results[0] > CARDINAL else 'not'} {ge} {CARDINAL}%."
                                else: 
                                    text = f"{'Yes' if results[0] < CARDINAL else 'No'}, the increase of {kpi} was {'' if results[0] < CARDINAL else 'not'} {le} {CARDINAL}%."         
                        if text == "":
                            dispatcher.utter_message(text="No results found for your query.")
                        else:
                            dispatcher.utter_message(text=text)
                            if is_prediction:
                                dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")
                    else:
                        dispatcher.utter_message(text="Only single line result is supported for a 'yes or no' question.")
                
                else:
                    if len(results) <= 20:
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    else:
                        text += f"In total {len(results)} returned. Here are the first 20 results:  \n"
                        results = results[:20]
                        for result in results:
                            text += f"{result[0]}, {round(result[1]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[1],1)}{'%' if (kpi == 'Percentage_of_target') or ('%' in CARDINAL[0]) else ''}  \n"
                    if text == "":
                        dispatcher.utter_message(text="No results found for your query.")
                    else:
                        dispatcher.utter_message(text=text)
                        if is_prediction:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")
        except Exception as e:
            print("action_execute_filter_query:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
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
        DATE = tracker.get_slot("DATE")
        CARDINAL = tracker.get_slot("CARDINAL")
        top = tracker.get_slot("top")
        bottom = tracker.get_slot("bottom")
        max = tracker.get_slot("max")
        min = tracker.get_slot("min")
        increase = tracker.get_slot("increase")
        q_type = tracker.get_slot("q_type") 
        try:
            translator = QueryTranslator()
            make_query = Querymethods()
            if len(DATE) == 1:
                is_prediction = translator.kpi_is_prediction(DATE[0], False)
            else:
                is_prediction = False

            # in case the intent 'agg' was wrongly classified as 'limit
            if not CARDINAL:
                CARDINAL = [1]

            q = translator.limit_query(kpi, place, DATE, CARDINAL, top, bottom, increase, max, min)
            print('limit: ', q)

            results = make_query.execute_sqlquery(q[0])

            if q_type == "ask-place":
                res =""
                if results:
                    for result in results:
                        res += f"{result[1]}, {round(result[0]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                    dispatcher.utter_message(text=res)
                    if is_prediction:
                        if tracker.get_slot('language') == 'german':
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                        else:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")

                else:
                    if tracker.get_slot('language') == 'german':
                        dispatcher.utter_message(text='Es wurde kein Ergebniss für Ihre Frage gefunden')
                    else:
                        dispatcher.utter_message(text="No results found for your query.")

            else:
                res =""
                if results:
                    for result in results:
                        res += f"{result[1]}, {round(result[0]) if kpi in ('Locations', 'Charging_stations', 'Charging_points') else round(result[0],1)}{'%' if kpi == 'Percentage_of_target' else ''}  \n"

                    dispatcher.utter_message(text=res)
                    if is_prediction:
                        if tracker.get_slot('language') == 'german':
                            dispatcher.utter_message(text="Bitte beachten Sie, dass die Datenquelle normalerweise verzögert die Daten bereit stellt, der Letzte verfügbare Monat ist September 2022, also handelt es sich hierbei um eine Vorhersage.")
                        else:
                            dispatcher.utter_message(text="Please be aware that the source data usually lags and the latest available month is May 2022, so this is a prediction based on past values.")

                else:
                    if tracker.get_slot('language') == 'german':
                        dispatcher.utter_message(text= 'Es wurde kein Ergebniss für Ihre Frage gefunden.')
                    else:
                        dispatcher.utter_message(text="No results found for your query.")


        except Exception as e:
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)
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
            if slot_name not in ("stored_slots", "language"):
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
            make_query = Querymethods()
            # get one random document from Questionbase
            result = make_query.random_access("Questionbase")
            if result:
                return [SlotSet("quiz_question", result)]
        except Exception as e:
            print("action_check_quiz:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
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
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=f"Was ist die {quiz['name']} von {quiz['place']} in {quiz['time']}? Geben Sie die Zahl in dem Format '123' für ganze Zahlen oder '123.45' für Kommazahlen ein. Falls Sie dies nicht wissen oder nicht antworten wollen, schreiben Sie 'skip'. ")
            else:
                dispatcher.utter_message(text=f"What is the {quiz['name']} of {quiz['place']} in {quiz['time']}? Enter the number using the format '123' for integer or '123.45' for decimal. If you don't know or don't want to answer it, please type 'skip'. ")

class NoQuiz(Action):
    def name(self) -> Text:
        return "action_no_quiz"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text= f"In diesem Moment sind uns die Fragen ausgegangen😉. ")
        else:
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
        with open('/app/actions/lookup/New_KPI.txt', 'a') as f:
            f.write(str(kpi_name)+'\n')

class ActionNewKPIConfirm(Action): 

    def name(self) -> Text:
        return "action_new_kpi_confirm"

    def run(self, dispatcher, tracker, domain):
        kpi_name = tracker.get_slot("kpi_name")
        kpi_definition = tracker.get_slot("kpi_definition")
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"kpi_name: {kpi_name}  \n kpi_definition: {kpi_definition}",
            buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
            ])
        else:
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
            make_query = Querymethods()
            client = make_query.set_mongodb_connect()
            db = client['emobility']
            new_kpi_definition = db['new_kpi_definition']
            new_kpi_definition.insert_one({"kpi_name": kpi_name, "kpi_definition": kpi_definition})
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text="Gut, Ich habe dies in unsere Wissensdatenbank eingefügt.")
            else:
                dispatcher.utter_message(text="Good. I have put it in the knowledgebase.")

        except Exception as e:
            print(e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)

        return 

class ActionCheckPredefinedAndUserdefined(Action):

    def name(self) -> Text:
        return "action_check_predefined_and_userdefined"

    
    def run(self, dispatcher, tracker, domain):
        kpi = tracker.get_slot("kpi")
        with open('/app/actions/lookup/New_KPI.txt', 'r', encoding='utf8') as f:
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
        if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text="Es tur mir leid, ich habe diese Information nicht. Können Sie mir damit helfen?",
            buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
            ])
        else:
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
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text="Es tur mir leid, ich konnte keine Informationen über diesen KPI in unserer Wissensbasis finden. Möchten sie einen neuen KPI definieren?",
            buttons = [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
            ])
        else:
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
        current_time = tracker.get_slot("DATE")
        
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
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text="Danek! Die Information ist nun in unserer Wissensbasis😊")
            else:
                dispatcher.utter_message(text="Thank you! The knowledge is now in the knowledgebase😊")
        except Exception as e:
            print("action_store_knowledge:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
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
        DATE = tracker.get_slot("DATE")

        try:
            # user skip
            if tracker.get_slot("has_skip"):
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message('Ok, ich werde die Frage zu unsere Fragendatenbank hinzufügen.')
                else:
                    dispatcher.utter_message(text="Ok, I will add the question(s) into our Questionbase.")
                args_dict = tracker.get_slot("args_dict")

                for k,v in args_dict.items():
                    if v == 'skip':
                        data.append({"name": k, "place": place[0], "time": DATE[0]})
            # user deny
            else:
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(text="Ok, ich werden die Frage als unbeantwortet markieren und zu unserer Fragendatenbank hinzufügen.")
                dispatcher.utter_message(text="Ok, I will label the questions as unanswered and put them into Questionbase.")
                args_to_be_asked = tracker.get_slot("args_to_be_asked")

                
                for arg in args_to_be_asked:
                    data.append({"name": arg, "place": place[0], "time": DATE[0]})

            make_query = Querymethods()
            make_query.insert_docu("Questionbase", data)
        except Exception as e:
            print("action_store_questions:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
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

class ActionQuizFinished(Action):
    '''
    Quiz finished. Remove it from Questionbase and add it into Statistics

    Reference: "action_ask_quiz_1" line 200
    '''

    def name(self) -> Text:
        return "action_quiz_finished"

    def run(self, dispatcher, tracker, domain):
        # has_skip_quiz = tracker.get_slot("has_skip_quiz")
        quiz_question = tracker.get_slot("quiz_question")

        quiz_1 = tracker.get_slot("quiz_1")

        try:
            if quiz_1 != "skip":
                # remove
                make_query = Querymethods()
                make_query.remove_docu("Questionbase", quiz_question["_id"])
                entries_to_be_added = []
                params_to_be_added = []
                # add
                if make_query.find_value("statistics", "name", quiz_question["name"], "entries"):
                    entries_to_be_added = [{"name": quiz_question["name"], "entries": (quiz_1, quiz_question["place"], quiz_question["time"])}]
                else:
                    params_to_be_added = [{"name": quiz_question["name"], "entries": [(quiz_1, quiz_question["place"], quiz_question["time"])]}]
                
                map_data_format = MapDataFormat()
                # add new params
                if params_to_be_added:
                    map_data_format.add_new_params(params_to_be_added)
                # add new entries
                if entries_to_be_added:
                    map_data_format.add_new_entries(entries_to_be_added)
                # response
                if tracker.get_slot('language') == 'germam':
                    dispatcher.utter_message(text="Vielen Dank, Die Information ist jetzt in der Wissensbasis.")
                else:
                    dispatcher.utter_message(text="Thank you! The knowledge is now in the knowledgebase😄")
            else:
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(text="Das war schon ne schwierige Frage😜")
                else:
                    dispatcher.utter_message(text="It's a hard question, I know😜")
        except Exception as e:
            print("action_quiz_finished:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)

        return []

class ActionAskAnotherQuiz(Action):
    '''
    check if user skips some questions and predicts action accordingly.
    '''

    def name(self) -> Text:
        return "action_ask_another_quiz"

    def run(self, dispatcher, tracker, domain):

        # ask user whether to have another quiz question
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text="Würden Sie gerne ein weiteres Quiz machen? 🤓",
            buttons= [
                {"title": "Ja","payload": "/affirm"},
                {"title": "Nein", "payload": "/deny"}
            ])
        else:
            dispatcher.utter_message(text="Would you like to have another quiz? 🤓",
            buttons= [
                {"title": "yes","payload": "/affirm"},
                {"title": "no", "payload": "/deny"}
            ])

        return []
        
# ------------------------------------------------------
# Below are the actions of nearby search and nearest search
# ------------------------------------------------------
class AskForAddress(Action):
    def name(self) -> Text:
        return "action_ask_address"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Was ist die Adresse von dem Zentrum des Suchgebiets?")
        else:
            dispatcher.utter_message(text=f"What is the address of center of the search area?")
        return []

class AskForRadius(Action):
    def name(self) -> Text:
        return "action_ask_radius"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Wie groß soll der Suchradius(in Metern) sein?")
        else:
            dispatcher.utter_message(text=f"How many meters should the search area's radius be?")
        return []

class ActionNearbySearch(Action):
    '''
    perform a nearby search
    '''

    def name(self) -> Text:
        return "action_nearby_search"

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text="Ihre Anfrage wird bearbeitet...Dies kann einige Sekunden dauern.")
        else:
            dispatcher.utter_message(text="Your query is in process...This might take a few seconds.")
        address = tracker.get_slot("address")
        radius = tracker.get_slot("radius")
        try:
            my_search = NearbySearch(6000, address)
            found_nodes, num_found_nodes = my_search.radius_search(radius)
            my_search.display_map(found_nodes)
            results = ""
            if found_nodes:
                for i in range(len(found_nodes)):
                    results += f"{i+1}. {found_nodes[i]['addr']}({round(found_nodes[i]['dist'], 2)}km)  \n"
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(ext=f"Insgesamt wurden, {num_found_nodes} Ladestationen in einem Radius von {radius} metern gefunden:  \n"+results)
                else:
                    dispatcher.utter_message(text=f"In total, {num_found_nodes} charging stations were found within {radius} meters:  \n"+results)
                # dispatcher.utter_message(image="./my_map.html")
            else:
                if tracker.get_slot('language') == 'german':
                    dispatcher.utter_message(text="Es wurden keine Ladestationen gefunden. Versuchen Sie doch ihr Glück mit einem anderen Ort oder Radius")
                else:
                    dispatcher.utter_message(text="No charging stations were found. Try your luck with another place/radius.")
        except Exception as e:
            print(e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=f"Es tut mir leid, ein Fehler ist aufgetreten. Unsere Dienstleistungen basieren auf OpenStreetMap und dies bedeuted, dass momentan vielleicht zu viele Leute versuchen Informationen abzurufen. Bitte versuchen sie es später erneut oder wählen sie einen anderen Ort oder Radius.")
            else:
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
#         if tracker.get_slot('language') == 'german':
#             dispatcher.utter_message(text="Ihr Anfrage wird bearbeitet...Dies kann einige Sekunden dauern.")
#         else:
#             dispatcher.utter_message(text="Your query is in process...This might take a few seconds.")
#         address = tracker.latest_message['address']
#         radius_list = [500, 1000, 3000, 5000]
#         try:
#             for radius in radius_list:
#                 my_search = NearbySearch(6000, address)
#                 found_nodes, num_found_nodes = my_search.radius_search(radius)
#                 if found_nodes:
#                     if tracker.get_slot('language') == 'german':
#                         dispatcher.utter_message(text=f"Die nächste Ladestation ist {found_nodes[0]} und damit {found_nodes[1]} meter entfernt.")
#                     else:
#                         dispatcher.utter_message(text=f"The nearest charging station is {found_nodes[0]}, which is {found_nodes[1]} meters away.")
#                     break
#             if not found_nodes:
#                 if tracker.get_slot('language') == 'german':
#                     dispatcher.utter_message(text="Es giebt keine Ladestationen in einem Radius von 5 km")
#                 else:
#                     dispatcher.utter_message(text="There are no charging stations found within radius of 5 km.")
#         except:
#             if tracker.get_slot('language') == 'german':
#                 dispatcher.utter_message(text=f"Es tut mir leid, ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.")
#             else:
#                 dispatcher.utter_message(text=f"Sorry, an issue occurred. Please try again later.")

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
        dates = tracker.get_latest_entity_values("DATE")
        places = tracker.get_latest_entity_values("place")
        cardinals = tracker.get_latest_entity_values("CARDINAL")

        slotset = []

        slot_date = [date.value() for date in dates]
        if len(slot_date) > 1:
            slotset.append([SlotSet("DATE", slot_date)])
        slot_place = [place.value() for place in places]
        if len(slot_place) > 1:
            slotset.append([SlotSet("place", slot_place)])
        slot_cardinal = [cardinal.value() for cardinal in cardinals]
        if len(slot_cardinal) > 1:
            slotset.append([SlotSet("CARDINAL", slot_place)])

        return slotset

# ------------------------------------------------------
# Below are the actions for 'add faqs'
# ------------------------------------------------------        
class AskForFaqsQ(Action):
    def name(self) -> Text:
        return "action_ask_faqs_q"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Wie lautet die Frage, die Sie zum FAQ hinzufügen wollen?")
        else:
            dispatcher.utter_message(text=f"What is the question you want to add to the FAQs?")
        return []

class AskForFaqsA(Action): 

    def name(self) -> Text:
        return "action_ask_faqs_a"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text=f"Wie lautet die Antwort?")
        else:
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
            make_query = Querymethods()
            client = make_query.set_mongodb_connect()
            db = client['emobility']
            faqs = db['FAQs']
            faqs.insert_one({"question": faqs_q, "answer": faqs_a})
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text="Neues FAQ wurde hinzugefügt! Ihr FAQ wird nun anderen nutzen präsentiert 😄")
            else:
                dispatcher.utter_message(text="New FAQ added! Your FAQ will now be presented to other users 😄")

        except Exception as e:
            print("action_add_faqs_finished:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)

        return []

# ------------------------------------------------------
# Below are the actions for 'emobility faqs'
# ------------------------------------------------------  
class ActionGiveFAQsFinished(Action):
    def name(self) -> Text:
        return "action_give_faqs_finished"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        try:
            # randomly pick one in mongodb
            make_query = Querymethods()
            # get one random document from Questionbase
            result = make_query.random_access("FAQs")
            dispatcher.utter_message(text=f"Q: {result['question']}  \n A: {result['answer']}")

        except Exception as e:
            print("action_give_faqs_finished:",e)
            if tracker.get_slot('language') == 'german':
                dispatcher.utter_message(text=SORRY_MESSAGE_GER)
            else:
                dispatcher.utter_message(text=SORRY_MESSAGE)

        return []

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
        yes_or_no_words = ['was', 'is', 'do', 'does', 'did', 'are', 'were', 'will', 'would','ist', 'wird', 'waren', 'sind', 'werden']
        ask_number_words = ['what', 'how many','was', 'wie viele','wie viel']
        text = tracker.latest_message['text']
        if text.split()[0].lower() in yes_or_no_words:
            return [SlotSet("q_type", "ask-yes-or-no")]
        elif "state" in text or "count" in text:
            if text.split()[0].lower() in ask_number_words:
                return [SlotSet("q_type", "ask-number")]
            else:
                return [SlotSet("q_type", "ask-place")]
        elif "operator" in text or "provider" in text:
            return [SlotSet("q_type", "ask-provider")]
        else:
            return [SlotSet("q_type", "ask-number")]



# ------------------------------------------------------
# Handle disambiguate
# ------------------------------------------------------  

class ActionDisambiguate(Action):
    # always be triggered after action 'nlu_fallback'
    def name(self) -> Text:
        return "action_disambiguate"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # get the first 2 intents that caused the ambiguity
        intent_ranking = tracker.latest_message['intent_ranking']
        #     "intent_ranking": [{nlu_fallback, con}, {intent_1, con}, {intent_2, con}]
        # asking user to choose 1 from the 2 options by buttons
        if tracker.get_slot('language') == 'german':
            dispatcher.utter_message(text="Welche Intention stimmt mit ihrerer Anfrage überein?",
            buttons= [
                {"title": f"{intent_ranking[1]}","payload": f"/{intent_ranking[1]}"},
                {"title": f"{intent_ranking[2]}", "payload": f"/{intent_ranking[2]}"}
            ])
        else:
            dispatcher.utter_message(text="Which intent below matches your query better?",
            buttons= [
                {"title": f"{intent_ranking[1]}","payload": f"/{intent_ranking[1]}"},
                {"title": f"{intent_ranking[2]}", "payload": f"/{intent_ranking[2]}"}
            ])        

        return []


# ------------------------------------------------------
# Custom restart
# ------------------------------------------------------  

class ActionRestarted(Action):

    def name(self):
        return "action_restart"

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot('language') == 'german':
            return [Restarted(), FollowupAction('action_set_ger')]
        else:
            return [Restarted(), FollowupAction('action_set_en')]


# ------------------------------------------------------
# set language during conversation
# ------------------------------------------------------  
class ActionSetEN(Action):

    def name(self):
        return "action_set_en"

    def run(self, dispatcher, tracker, domain):
        # parse_data = {"intent": {"name": "welcome_message","confidence": 1}, "entity": {"name":"language","value":"english"}}
        return [SlotSet("language", "english"), FollowupAction('action_listen')]

class ActionSetGER(Action):

    def name(self):
        return "action_set_ger"

    def run(self, dispatcher, tracker, domain):
        # parse_data = {"intent": {"name": "welcome_message","confidence": 1}, "entity": {"name":"language","value":"german"}}
        return [SlotSet("language", "german"), FollowupAction('action_listen')]

