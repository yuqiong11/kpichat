import stat
from rasa_sdk import Action, Tracker, FormValidationAction
import datetime


class CheckTime:
    def __init__(self):
        pass

    def time_mapping(self, time, special_period_expression):
        return self.convert_time(time, special_period_expression)

    @staticmethod
    def time_out_of_range(time):
        return time > '202301' or time < '201701'

    def kpi_is_prediction(self, time, special_period_expression):
        return self.time_mapping(time, special_period_expression) > '202205'

    def convert_time(self,old_time, special_period_expression):
        '''
        special period expression means period+len(DATE)==1, e.g. last year instead of from \n
        01.2021 to 01.2022, where len(DATE) ==2 
        Convert user-expressed time format into a unified format
        input: str
        output: str
        '''

        slot_year= ""
        slot_month=""

        current_year = str(datetime.date.today().year)  # '2020'
        current_month = str(datetime.date.today().month)  # '6'

        # original
        months_of_text = [
            'Jan', 'Feb', 'Mar',
            'Apr', 'May', 'Jun', 
            'Jul', 'Aug', 'Sept',
            'Oct', 'Nov', 'Dec',
        ]
        months_of_text_ger = [
            'Jan', 'Feb', 'Mär',
            'Apr', 'Mai', 'Jun', 
            'Jul', 'Aug', 'Sept',
            'Okt', 'Nov', 'Dez',
        ]
        months_of_text_numbered = [
            'First', 'Second', 'Third',
            'Fourth', 'Fifth', 'Sixth',
            'Seventh', 'Eighth', 'Ninth',
            'Tenth', 'Eleventh', 'Twelfth'
        ]
        months_of_text_numbered_ger = [
            'Erster', 'Zweiter', 'Dritter',
            'Vierter', 'Fünfter', 'Sechster',
            'Siebter', 'Achter', 'Neunter',
            'Zehnter', 'Elfter', 'Zwölfter'
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
        years = ['2023','2022', '2021', '2020', '2019', '2018', '2017']
        special_words_01 = ['beginning', 'first','erste', 'anfang']
        special_words_02 = ['end', 'twelfth', 'last month of','letzte monat von','ende']
        special_words_03 = ['last year', 'previous year', 'letztes jahr']
        special_words_04 = ['next year','nächstes jahr']
        special_words_05 = ['now', 'jetzt', 'moment', 'today', 'heute']

        # mapping
        if special_period_expression:
            # period
            if old_time.lower() in ('last year','previous year', 'past year', 'letztes jahr', 'letzten jahr', 'letztem jahr'):
                mapped_time_end = str(int(current_year)-1)+'12'
                mapped_time_start = str(int(current_year)-2)+'12'
            elif old_time in years:
                # 2020, 2021, 2022
                mapped_time_end = old_time+'12'
                mapped_time_start = old_time+'12'
            elif old_time.lower() in ('last 2 years', 'last two years', 'past 2 years', 'last 2 yrs', 'past 2 yrs','letzten zwei jahre','letzten zwei jahren','letzten beiden jahren','letzten beiden jahre','letzten 2 jahre', 'letzten 2 jahren'):
                if int(current_month) < 10 :
                    mapped_time_end = str(int(current_year)-1)+'0'+current_month
                    mapped_time_start = str(int(current_year)-3)+'0'+current_month
                else:
                    mapped_time_end = str(int(current_year)-1)+current_month
                    mapped_time_start = str(int(current_year)-3)+current_month
            elif old_time.lower() in ('last 3 years', 'last three years', 'past 3 years', 'last 3 yrs', 'past 3 yrs', 'letzten drei jahre', 'letzten drei jahren', 'letzten 3 jahre', 'letzten 3 jahren'):
                if int(current_month)  < 10: 
                    mapped_time_end = str(int(current_year)-1)+'0'+current_month
                    mapped_time_start = str(int(current_year)-4)+'0'+current_month
                else:
                    mapped_time_end = str(int(current_year)-1)+current_month
                    mapped_time_start = str(int(current_year)-4)+current_month
            elif old_time.lower() in ('last 4 years', 'last four years', 'past 4 years', 'last 4 yrs', 'past 4 yrs', 'letzten vier jahre', 'letzten vier jahren', 'letzten 4 jahre', 'letzten 4 jahren'):
                if int(current_month) < 10:
                    mapped_time_end = str(int(current_year)-1)+'0'+current_month
                    mapped_time_start = str(int(current_year)-5)+'0'+current_month
                else:
                    mapped_time_end = str(int(current_year)-1)+current_month
                    mapped_time_start = str(int(current_year)-5)+current_month
            elif old_time.lower() in ('last 5 years', 'last five years', 'past 5 years', 'last 5 yrs', 'past 5 yrs', 'letzten 5 jahre', 'letzten 5 jahren', 'letzten fünf jahre', 'letzten fünf jahren'):
                if int(current_month) < 10:
                    mapped_time_end = str(int(current_year)-1)+'0'+current_month
                    mapped_time_start = str(int(current_year)-6)+'0'+current_month
                else:
                    mapped_time_end = str(int(current_year)-1)+current_month
                    mapped_time_start = str(int(current_year)-6)+current_month
            elif old_time.lower() in ('last month', 'past month', 'previous month','letzten monat'):
                if current_month == '01':
                    mapped_time_end = str(int(current_year)-1)+'12'
                    mapped_time_start = str(int(current_year)-1)+'11'
                elif current_month == '02':
                    mapped_time_end = current_year+'01'
                    mapped_time_start = str(int(current_year)-1)+'12'
                else:
                    if int(current_month) <= 10 :                                   
                        mapped_time_end = current_year+'0'+str(int(current_month)-1)
                        mapped_time_start = current_year+'0'+str(int(current_month)-2)
                    else:
                        mapped_time_end = current_year+str(int(current_month)-1)
                        mapped_time_start = current_year+str(int(current_month)-2)
            else:
                # increase in May 2020 or 05.2020
                # copy from timepoint
                if old_time[:4] in years and old_time[4:6] in months_of_number_3:
                    mapped_time = old_time
                elif old_time[:2] in months_of_number_3 and old_time[2:6] in years:
                    mapped_time = old_time[2:6] + old_time[:2]
                else:
                    #search for year
                    for i in range(len(special_words_03)):
                        if special_words_03[i] in old_time.lower():
                            slot_year = str(int(datetime.date.today().year)-1)
                    if slot_year == "":
                        for i in range(len(special_words_04)):
                            if special_words_04[i] in old_time.lower():
                                slot_year = str(int(datetime.date.today().year)+1)
                    if slot_year == "":
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
                            if word in old_time.lower():
                                slot_month='12'

                    if slot_month == "":
                        for i in range(len(special_words_05)):
                            if special_words_05[i] in old_time.lower():
                                current_month = datetime.datetime.now().month
                                slot_year=str(datetime.datetime.now().year)
                                if current_month < 10:
                                    slot_month='0'+str(current_month)
                                else:
                                    slot_month=str(current_month)

                    if slot_month == "":    
                        if 'last month' in old_time.lower() or 'letzter monat' in old_time.lower() or 'letzten monat' in old_time.lower():
                            current_date = datetime.datetime.now()
                            d = datetime.timedelta(days = 30)
                            required_date = current_date - d
                            slot_year=str(required_date.year)
                            if required_date.month < 10:
                                slot_month='0'+str(required_date.month)
                            else:
                                slot_month=str(required_date.month)

                    if slot_month == "":
                        if 'next month' in old_time.lower() or 'nächster monat' in old_time.lower() or 'nächsten monat' in old_time.lower():
                            current_date = datetime.datetime.now()
                            d = datetime.timedelta(days = 30)
                            required_date = current_date + d
                            slot_year=str(required_date.year)
                            if required_date.month < 10:
                                slot_month='0'+str(required_date.month)
                            else:
                                slot_month=str(required_date.month)  


                    if slot_month == "":
                            for i in range(len(months_of_text_numbered)):
                                if months_of_text_numbered[i].lower() in old_time.lower() or months_of_text_numbered_ger[i].lower() in old_time.lower():
                                    if i >= 9:
                                        slot_month = str(i+1)
                                    else:
                                        slot_month = '0'+str(i+1)

                    if slot_month == "":
                        for i in range(len(months_of_text)):
                            if months_of_text[i].lower() in old_time.lower() or months_of_text_ger[i].lower() in old_time.lower():
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
                    if slot_month == '01':
                        # 202001-201912 
                        mapped_time_start, mapped_time_end = str(int(slot_year)-1)+'12', mapped_time
                    else:
                        # 202005-202004
                        mapped_time_start, mapped_time_end = str(int(mapped_time)-1), mapped_time              
            return mapped_time_start, mapped_time_end
        else:
            # timepoint        
            if old_time[:4] in years and old_time[4:6] in months_of_number_3:
                mapped_time = old_time
            elif old_time[:2] in months_of_number_3 and old_time[2:6] in years:
                mapped_time = old_time[2:6] + old_time[:2]
            else:
                #search for year
                for i in range(len(special_words_03)):
                    if special_words_03[i] in old_time.lower():
                        slot_year = str(int(datetime.date.today().year)-1)
                if slot_year == "":
                    for i in range(len(special_words_04)):
                        if special_words_04[i] in old_time.lower():
                            slot_year = str(int(datetime.date.today().year)+1)
                if slot_year == "":
                    for year in years:
                        if year in old_time:
                            slot_year = year
                            break

                #search for month
                for word in special_words_01:
                    if word in old_time.lower():
                        slot_month='01'
                        break

                if slot_month == "":
                    for word in special_words_02:
                        if word in old_time.lower():
                            slot_month='12'

                if slot_month == "":
                    for i in range(len(special_words_05)):
                        if special_words_05[i] in old_time.lower():
                            current_month = datetime.datetime.now().month
                            slot_year=str(datetime.datetime.now().year)
                            if current_month < 10:
                                slot_month='0'+str(current_month)
                            else:
                                slot_month=str(current_month)

                if slot_month == "":    
                    if 'last month' in old_time.lower() or 'letzter monat' in old_time.lower() or 'letzten monat' in old_time.lower():
                        current_date = datetime.datetime.now()
                        d = datetime.timedelta(days = 30)
                        required_date = current_date - d
                        slot_year=str(required_date.year)
                        if required_date.month < 10:
                            slot_month='0'+str(required_date.month)
                        else:
                            slot_month=str(required_date.month)

                if slot_month == "":
                    if 'next month' in old_time.lower() or 'nächster monat' in old_time.lower() or 'nächsten monat' in old_time.lower():
                        current_date = datetime.datetime.now()
                        d = datetime.timedelta(days = 30)
                        required_date = current_date + d
                        slot_year=str(required_date.year)
                        if required_date.month < 10:
                            slot_month='0'+str(required_date.month)
                        else:
                            slot_month=str(required_date.month)  


                if slot_month == "":
                        for i in range(len(months_of_text_numbered)):
                            if months_of_text_numbered[i].lower() in old_time.lower() or months_of_text_numbered_ger[i].lower() in old_time.lower():
                                if i >= 9:
                                    slot_month = str(i+1)
                                else:
                                    slot_month = '0'+str(i+1)

                if slot_month == "":
                    for i in range(len(months_of_text)):
                        if months_of_text[i].lower() in old_time.lower() or months_of_text_ger[i].lower() in old_time.lower():
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

# test
#time_checker = CheckTime()
#print(time_checker.convert_time('heute', False))