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
        months_of_number = [
        '01.20', '02.20', '03.20', '04.20', '05.20', '06.20', '07.20', '08.20', '09.20', '10.20', '11.20', '12.20'    
        ]
        years = ['2022', '2021', '2020', '2019', '2018', '2017']
        special_words_01 = ['beginning', 'first']
        special_words_02 = ['end', 'twelfth', 'last month of']

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
                slot_year=str(required_date.year)
                if len(current_month) == 1:
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
            for i in range(len(months_of_number)):
                if months_of_number[i] in DATE:
                    if i >= 9:
                        slot_month = str(i+1)
                    else:
                        slot_month = '0'+str(i+1)
                    
        return [SlotSet("mapped_time", slot_year+slot_month)]
        


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


class ActionQueryConfirm(Action): 

    def name(self) -> Text:
        return "action_query_confirm"

    def run(self, dispatcher, tracker, domain):
        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")
        dispatcher.utter_message(text=f"the place is {place}, kpi is {kpi}, time is {mapped_time}?",
        buttons= [
            {"title": "yes","payload": "/affirm"},
            {"title": "no", "payload": "/deny"}
        ])
        return []
        

class ActionExecuteQuery(Action):
   def name(self) -> Text:
      return "action_execute_query"

   def run(self, dispatcher, tracker, domain):

        """
        runs when action_execute_query is triggered.
        
        """
        conn = Querymethods.set_connect()
        cur = conn.cursor()

        place = tracker.get_slot("place")
        mapped_time = tracker.get_slot("mapped_time")
        kpi = tracker.get_slot("kpi")

        if kpi == "Locations":
            q = f"SELECT no_total_locations FROM \"E-Mobility\".emo_historical WHERE state='{place}' AND month={mapped_time}; "
        elif kpi == "Charging stations":
            q = f"SELECT no_total_stations FROM \"E-Mobility\".emo_historical WHERE state='{place}' AND month={mapped_time}; "
        else:
            q = f"SELECT no_total_chargepoints FROM \"E-Mobility\".emo_historical WHERE state='{place}' AND month={mapped_time}; "

        cur.execute(q)
        result = cur.fetchall()
        if len(result) == 1:
            dispatcher.utter_message(text=str(result[0][0]))

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

    # def basic_kpis(self,
    #                dispatcher: CollectingDispatcher,
    #                tracker: Tracker,
    #                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    #     '''
        
    #     '''
    #     conn = self.set_connect()
    #     cur = conn.cursor()
    #     cur.execute(f"SELECT no_total_locations FROM \"E-Mobility\".emo_historical WHERE state={place} AND month=202112; ")


        

''' below are code snippets from concertbot'''
# from rasa_sdk import Action
# from rasa_sdk.events import SlotSet


# class ActionSearchConcerts(Action):
#     def name(self):
#         return "action_search_concerts"

#     def run(self, dispatcher, tracker, domain):
#         concerts = [
#             {"artist": "Foo Fighters", "reviews": 4.5},
#             {"artist": "Katy Perry", "reviews": 5.0},
#         ]
#         description = ", ".join([c["artist"] for c in concerts])
#         dispatcher.utter_message(text=f"{description}")
#         return [SlotSet("concerts", concerts)]


# class ActionSearchVenues(Action):
#     def name(self):
#         return "action_search_venues"

#     def run(self, dispatcher, tracker, domain):
#         venues = [
#             {"name": "Big Arena", "reviews": 4.5},
#             {"name": "Rock Cellar", "reviews": 5.0},
#         ]
#         dispatcher.utter_message(text="here are some venues I found")
#         description = ", ".join([c["name"] for c in venues])
#         dispatcher.utter_message(text=f"{description}")
#         return [SlotSet("venues", venues)]


# class ActionShowConcertReviews(Action):
#     def name(self):
#         return "action_show_concert_reviews"

#     def run(self, dispatcher, tracker, domain):
#         concerts = tracker.get_slot("concerts")
#         dispatcher.utter_message(text=f"concerts from slots: {concerts}")
#         return []


# class ActionShowVenueReviews(Action):
#     def name(self):
#         return "action_show_venue_reviews"

#     def run(self, dispatcher, tracker, domain):
#         venues = tracker.get_slot("venues")
#         dispatcher.utter_message(text=f"venues from slots: {venues}")
#         return []


# class ActionSetMusicPreference(Action):
#     def name(self):
#         return "action_set_music_preference"

#     def run(self, dispatcher, tracker, domain):
#         """Sets the slot 'likes_music' to true/false dependent on whether the user
#         likes music"""
#         intent = tracker.latest_message["intent"].get("name")

#         if intent == "affirm":
#             return [SlotSet("likes_music", True)]
#         elif intent == "deny":
#             return [SlotSet("likes_music", False)]
#         return []