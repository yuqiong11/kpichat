import stat
from rasa_sdk import Action, Tracker, FormValidationAction
import datetime


class CheckTime:
    def __init__(self):
        pass

    def time_mapping(self, time):
        return self.convert_time(time)

    @staticmethod
    def time_out_of_range(time):
        return time > '202301' or time < '201701'

    def kpi_is_prediction(self, time):
        return self.time_mapping(time) > '202204'

    def convert_time(self,old_time):
        '''
        Convert user-expressed time format into a unified format
        '''

        slot_year= ""
        slot_month=""

        # original
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

        # mapping
        if old_time[:4] in years and old_time[4:6] in months_of_number_3:
            mapped_time = old_time
        elif old_time[:2] in months_of_number_3 and old_time[2:6] in years:
            mapped_time = old_time[2:6] + old_time[:2]
        else:
            #search for year
            for year in years:
                if year in old_time:
                    slot_year = year
                    break

            #search for month
            for word in special_words_01:
                if word in old_time:
                    slot_month='01'
                    break

            if slot_month == "":
                for word in special_words_02:
                    if word in old_time:
                        slot_month='12'

            if slot_month == "":
                if old_time == 'now' or 'moment' in old_time:
                    current_month = datetime.datetime.now().month
                    slot_year=str(datetime.datetime.now().year)
                    if current_month < 10:
                        slot_month='0'+str(current_month)
                    else:
                        slot_month=current_month

            if slot_month == "":    
                if 'last month' in old_time:
                    current_date = datetime.datetime.now()
                    d = datetime.timedelta(days = 30)
                    required_date = current_date - d
                    slot_year=str(required_date.year)
                    if required_date.month < 10:
                        slot_month='0'+str(required_date.month)
                    else:
                        slot_month=required_date.month

            if slot_month == "":
                if 'next month' in old_time:
                    current_date = datetime.datetime.now()
                    d = datetime.timedelta(days = 30)
                    required_date = current_date + d
                    slot_year=str(required_date.year)
                    if required_date.month < 10:
                        slot_month='0'+str(required_date.month)
                    else:
                        slot_month=required_date.month  


            if slot_month == "":
                if 'second month' in old_time:
                    slot_month='02'
                    
            if slot_month == "":
                if 'third month' in old_time:
                    slot_month='03'

            if slot_month == "":
                for i in range(len(months_of_text)):
                    if months_of_text[i] in old_time:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)

            if slot_month == "":
                for i in range(len(months_of_number_1)):
                    if months_of_number_1[i] in old_time:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)

            if slot_month == "":
                for i in range(len(months_of_number_2)):
                    if months_of_number_2[i] in old_time:
                        if i >= 9:
                            slot_month = str(i+1)
                        else:
                            slot_month = '0'+str(i+1)

            mapped_time = slot_year+slot_month

        return mapped_time

