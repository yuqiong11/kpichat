from backend.db import QueryMethods
from backend.query_translator import QueryTranslator
from backend.rephrase import rephrase_text, generate_answer
from mappings.time_mapping import CheckTime

SORRY_MESSAGE = "I'm very sorry but something went wrong😵‍💫​ I will try to get it fixed soon🔧 Thanks for your patience!"


class QueryProcessor():
    pass

class AggQueryProcessor():
    def __init__(self, **slots):
        self.translator = QueryTranslator()
        self.executor = QueryMethods()
        self.time_checker = CheckTime()
        # self.text = text
        self.is_prediction = False
        for s_name, s_value in slots.items():
            setattr(self, s_name, s_value)
        
    def run_translation(self):
        # if len(self.time) == 1:
        #     converted_time = translator.time_mapping(self.time[0], False)
        # elif len(self.time) == 2:
        #     converted_time = translator.time_mapping(self.time[1], False)
        is_prediction, q = self.translator.agg_query(self.kpi, self.place, self.time, self.max, self.min, self.avg, self.geo_level, self.increase, self.charger_type, self.q_type)
        self.is_prediction = is_prediction
        return q
        
    def run_execution(self):
        q = self.run_translation()
        print(q)
        return self.executor.execute_sqlquery(q)

    def run_response(self):
        result = self.run_execution()

        print(result)

        return generate_answer(self.query,result)

        try:
            if self.q_type == "ask-number":
                if not self.avg:
                    if self.kpi == 'Chargepoints':
                        print('1')
                        text = f"The number of {self.charger_type if self.charger_type else ''} charging points in {self.place[0]} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0][0]))+"."
                    else:
                        print('2')
                        text = f"The {self.kpi} in {self.place[0]} {'' if self.time == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time == 'now' else 'was' } "+str(round(result[0][0],1))+f"{'%' if self.kpi == 'Percentage of target' else ''}"+"."            

                else:
                    if len(self.place) == 1:
                        if self.kpi == 'Chargepoints':
                            print('3')
                            text = f"The {self.avg} number of {self.charger_type if self.charger_type else ''} charging points of a  {'state' if 'state' in self.place[0].lower() else 'county'} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0][0]))+"."
                        else:
                            print('4')
                            text = f"The {self.avg} {self.kpi} of a  {'state' if 'state' in self.place[0].lower() else 'county'} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0][0],1))+'%'+"."

                    else:
                        if self.kpi == 'Chargepoints':
                            print('5')
                            text = f"The {self.avg} number of {self.charger_type if self.charger_type else ''} charging points of {self.place[0]} in {self.place[1]} {'' if self.time[0] == 'now' else 'in'} in {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0][0]))+"."
                        else:
                            print('6')
                            text = f"The {self.avg} {self.kpi} of {self.place[0]} in {self.place[1]} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0][0], 1))+f"{'%' if self.kpi == 'Percentage of target' else ''}"+"."

            elif self.q_type == "ask-place":
                if len(self.place) == 1:
                    if self.kpi == 'Chargepoints':
                        print('7')
                        text = f"{result[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} number of {self.charger_type if self.charger_type else ''} charging points {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was'} "+str(round(result[0][0]))+"."   
                    else:
                        if len(self.time) != 1:
                            print('8')
                            text = f"{result[0][1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} from {self.time[0]} to {self.time[1]}, which was "+str(round(result[0][0]))+"."              
                        else:
                            # result  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
                            print("result ", result)
                            print('9')
                            text = f"{result[0][1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} in {self.time[0]}, which was "+str(round(result[0][0]))+"."
                # else:
                #     if not self.increase:
                #         text = f"{result[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time == 'now' else 'was'} "+str(round(result[0],1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."

                else:
                    if self.kpi == 'Chargepoints':
                        print('10')
                        text = f"{result[1]} in {self.place[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} number of charging points {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0]))+"."
                    else:
                        if len(self.time) != 1:
                            print('11')
                            text = f"{result[1]} in {self.place[1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} from {self.time[0]} to {self.time[1]}, which was "+str(round(result[0]))+"."
                        else:
                            print('12')
                            text = f"{result[1]} in {self.place[1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} in {self.time[0]}, which was "+str(round(result[0]))+"."
                    # else:
                    #     text = f"{result[1]} in {self.place[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was' }"+str(round(result[0],1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."
            else:
                # general template
                print('13')
                text = f"{self.kpi}  is "+str(round(result[0]))  

            if self.is_prediction:
                text += " Please be aware this is the predicted value as the data for the time you queried is yet to be released."

        except Exception as e:
            print("action_execute_charger_operator_query:",e)
            text = SORRY_MESSAGE

        print(text)
        return rephrase_text(text)
        # return text

class CompareQueryProcessor():
    def __init__(self, **slots):
        self.translator = QueryTranslator()
        self.executor = QueryMethods()
        self.time_checker = CheckTime()
        self.is_prediction = False
        for s_name, s_value in slots.items():
            setattr(self, s_name, s_value)
        
    def run_translation(self):
        is_prediction, q = self.translator.compare_query(self.kpi, self.place, self.time, self.increase, self.charger_type, self.q_type)
        self.is_prediction = is_prediction
        return q
        
    def run_execution(self):
        q = self.run_translation()
        return self.executor.execute_sqlquery(q)

    def run_response(self):
        result = self.run_execution()
        result = result[0][0]

        print('CompareQuery ', result)
        return generate_answer(self.query, result)

        try:
            if self.kpi == 'Percentage_of_target':
                if self.increase:
                    print('20')
                    if result < 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(abs(result), 1)}% less {self.charger_type if self.charger_type else''} {self.kpi} than {self.place[1]} from {self.time[0]} to {self.time[1]}."
                    elif result > 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(result,1)}% more {self.charger_type if self.charger_type else''} {self.kpi} than {self.place[1]} from {self.time[0]} to {self.time[1]}."
                    else:
                        text = f"Both places {'have' if self.is_prediction else 'had'} equal {self.charger_type if self.charger_type else''} {self.kpi} from {self.time[0]} to {self.time[1]}."

                else:
                    print('21')
                    if result < 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(abs(result), 1)}% less {self.charger_type if self.charger_type else ''} {self.kpi} than {self.place[1]} in {self.time[0]}."
                    elif result > 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(abs(result), 1)}% more {self.charger_type if self.charger_type else ''} {self.kpi} than {self.place[1]} in {self.time[0]}."
                    else:
                        text = f"Both places {'have' if self.is_prediction else 'had'} equal {self.charger_type if self.charger_type else''} {self.kpi} in {self.time[0]}."
                        
            else:
                if self.increase:
                    print('14')
                    if result < 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(abs(result))} less {self.charger_type if self.charger_type else''} {self.kpi} than {self.place[1]} from {self.time[0]} to {self.time[1]}."
                    elif result > 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(result)} more {self.charger_type if self.charger_type else''} {self.kpi} than {self.place[1]} from {self.time[0]} to {self.time[1]}."
                    else:
                        text = f"Both places {'have' if self.is_prediction else 'had'} equal {self.charger_type if self.charger_type else''} {self.kpi} from {self.time[0]} to {self.time[1]}."

                else:
                    print('15')
                    if result < 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(abs(result))} less {self.charger_type if self.charger_type else ''} {self.kpi} than {self.place[1]} in {self.time[0]}."
                    elif result > 0:
                        text = f"{self.place[0]} {'has' if self.is_prediction else 'had'} {round(result)} more {self.charger_type if self.charger_type else ''} {self.kpi} than {self.place[1]} in {self.time[0]}."
                    else:
                        text = f"Both places {'have' if self.is_prediction else 'had'} equal {self.charger_type if self.charger_type else''} {self.kpi} in {self.time[0]}."
        
        except Exception as e:
            print("compare query:",e)
            text = SORRY_MESSAGE

        print(text)
        return rephrase_text(text)      
        # return text
class ChargerProviderQueryProcessor():
    def __init__(self, **slots):
        self.translator = QueryTranslator()
        self.executor = QueryMethods()
        self.time_checker = CheckTime()
        self.is_prediction = False
        for s_name, s_value in slots.items():
            setattr(self, s_name, s_value)
        
    def run_translation(self):
        is_prediction, q = self.translator.charger_operator_query(self.kpi, self.place, self.time, self.max, self.min, self.geo_level, self.increase, self.charger_type, self.operator, self.q_type)
        self.is_prediction = is_prediction
        return q
        
    def run_execution(self):
        q = self.run_translation()
        return self.executor.execute_sqlquery(q)

    def run_response(self):
        result = self.run_execution()
        return generate_answer(self.query,result)

        if not self.place:
            place = 'Germany'
        else:
            place = self.place[0]

        self.q_type = "ask-provider"

        print(self.q_type)
        try:
            text = ""
            if self.q_type == "ask-provider":
                if self.max or self.min:
                    print('16')
                    text = f"The {'strongest' if max else 'weakest'} operator in {place} is {result[0]} with {result[1]} {self.charger_type if self.charger_type else ''} charging points." 
                else:
                    length_result = len(result)
                    if length_result > 5:
                        print('17')
                        text = f"There were {length_result} operators in {place}, here are the top 5 with chargepoints number:  \n"
                        for row in result[:5]:
                            text += f"{row[0]}, {round(row[1])}  \n"
                    else:
                        print('18')
                        text = f"There are {len(result)} operators in {place}:  \n"
                        for row in result:
                            text += f"{row[0]}, {round(row[1])}  \n"                

            else:  
                print('19')         
                for row in result:
                    text += f"{row[0]}, {round(row[1])}  \n"    

        except Exception as e:
            print("action_execute_charger_operator_query:",e)
            text = SORRY_MESSAGE

        print(text)
        return rephrase_text(text)
        # return text































# class LimitQueryProcessor():
#     def __init__(self, text, **slots):
#         self.translator = QueryTranslator()
#         self.executor = QueryMethods()
#         self.time_checker = CheckTime()
#         self.text = text
#         self.is_prediction = False
#         for s_name, s_value in slots:
#             self.s_name = s_value
        
#     def run_translation(self):
#         # if len(self.time) == 1:
#         #     converted_time = translator.time_mapping(self.time[0], False)
#         # elif len(self.time) == 2:
#         #     converted_time = translator.time_mapping(self.time[1], False)
#         is_prediction, q = self.translator.agg_query(self.kpi, self.place, self.time, self.max, self.min, self.avg, self.increase)
#         self.is_prediction = is_prediction
#         return q
        
#     def run_execution(self):
#         q = self.run_translation()
#         return self.executor.execute_sqlquery(q)

#     def run_response(self):
#         result = self.run_execution()
#         q_type = self.query_type()
#         latest_timestamp = self.get_latest_timestamp()


#         if q_type == "ask-number":
#             if not self.avg:
#                 if self.kpi == 'Chargepoints':
#                     text = f"The number of {self.charger_type if self.charger_type else ''} {self.kpi} in {self.place[0]} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0]))+"."
#                 else:
#                     text = f"The {self.kpi} in {self.place[0]} {'' if self.time == 'now' else 'in'} in {self.time[0]} {'is' if self.is_prediction or self.time == 'now' else 'was' } "+str(round(result[0],1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."            

#             else:
#                 if len(self.place) == 1:
#                     if self.kpi == 'Chargepoints':
#                         text = f"The {self.avg} number of {self.charger_type if self.charger_type else ''} {self.kpi} of a  {'state' if 'state' in self.place[0].lower() else 'county'} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0]))+"."
#                     else:
#                         text = f"The {self.avg} {self.kpi} of a  {'state' if 'state' in self.place[0].lower() else 'county'} {'' if self.time[0] == 'now' else 'in'} {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0],1))+'%'+"."

#                 else:
#                     if self.kpi == 'Chargepoints':
#                         text = f"The {self.avg} number of {self.charger_type if self.charger_type else ''} {self.kpi} of {self.place[0]} in {self.place[1]} {'' if self.time[0] == 'now' else 'in'} in {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0]))+"."
#                     else:
#                         text = f"The {self.avg} {self.kpi} of {self.place[0]} in {self.place[1]} {'' if self.time[0] == 'now' else 'in'} in {self.time[0]} {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0], 1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."

#         elif q_type == "ask-place":
#             if len(self.place) == 1:
#                 if self.kpi == 'Chargepoints':
#                     text = f"{result[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} number of {self.charger_type if self.charger_type else ''} {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was'} "+str(round(result[0]))+"."   
#                 else:
#                     if len(self.time) != 1:
#                         text = f"{result[0][1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} from {self.time[0]} to {self.time[1]}, which was "+str(round(result[0][0]))+"."              
#                     else:
#                         # result  [(Decimal('51.6856234636988'), 'Stadtkreis Stuttgart')]
#                         print("result ", result)
#                         text = f"{result[0][1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} in {self.time[0]}, which was "+str(round(result[0][0]))+"."
#                 else:
#                     if not self.increase:
#                         text = f"{result[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time == 'now' else 'was'} "+str(round(result[0],1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."

#             else:
#                 if self.kpi == 'Chargepoints':
#                     text = f"{result[1]} in {self.place[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} {self.charger_type if self.charger_type else ''} number of {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was' } "+str(round(result[0]))+"."
#                     else:
#                         if len(self.time) != 1:
#                             text = f"{result[1]} in {self.place[1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} from {self.time[0]} to {self.time[1]}, which was "+str(round(result[0]))+"."
#                         else:
#                             text = f"{result[1]} in {self.place[1]} had the {self.max if self.max else ''}{self.min if self.min else ''} increase of {self.kpi} in {self.time[0]}, which was "+str(round(result[0]))+"."
#                 else:
#                     text = f"{result[1]} in {self.place[1]} {'has' if self.time[0] == 'now' else 'had'} the {self.max if self.max else ''}{self.min if self.min else ''} {self.kpi} {'' if self.time[0] == 'now' else 'in'} {self.time[0]}, which {'is' if self.is_prediction or self.time[0] == 'now' else 'was' }"+str(round(result[0],1))+f"{'%' if self.kpi == 'Percentage_of_target' else ''}"+"."
#         else:
#             # general template
#             text = f"{self.kpi}  is "+str(round(result[0]))  


#     def query_type(self):
#         yes_or_no_words = ['was', 'is', 'do', 'does', 'did', 'are', 'were', 'will', 'would']
#         ask_number_words = ['what', 'how many']
        
#         if self.text.split()[0].lower() in yes_or_no_words:
#             return "ask-yes-or-no"
#         elif "state" in self.text or "count" in self.text:
#             if self.text.split()[0].lower() in ask_number_words:
#                 return "ask-number"
#             else:
#                 return "ask-place"
#         elif "operator" in self.text or "provider" in self.text:
#             return "ask-provider"
#         else:
#             return "ask-number"




#     def query_type(self):
#         yes_or_no_words = ['was', 'is', 'do', 'does', 'did', 'are', 'were', 'will', 'would']
#         ask_number_words = ['what', 'how many']
        
#         if self.text.split()[0].lower() in yes_or_no_words:
#             return "ask-yes-or-no"
#         elif "state" in self.text or "count" in self.text:
#             if self.text.split()[0].lower() in ask_number_words:
#                 return "ask-number"
#             else:
#                 return "ask-place"
#         elif "operator" in self.text or "provider" in self.text:
#             return "ask-provider"
#         else:
#             return "ask-number"