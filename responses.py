# response templates
# based on intent, type of question



class Generateresponses():
    def __init__(self, max, min, avg, kpi, place, DATE, increase, result):
        self.max = max

    def assign_response(responses, question_type, intent):
        if intent == "agg_query":
            return responses['agg']




RESPONSES = {
    'agg':
    {
        'absolute':
        {
            'plain': 'kh',
            'max-min-avg': f"The {max if max != None else ''}{min if min != None else ''}{avg if avg != None else ''} number of {kpi} in {'' if place.lower() != ('state' or 'county') else 'a'} {place} {'' if DATE == 'now' else 'in'} {DATE} is "+str(round(result[0]) if kpi != 'Percentage of target' else round(result[0],1))+f"{'%' if kpi == 'Percentage of target' else ''}"+".",
        },
        'increase':
        {
            'plain': 'kh, percentage',
            'max-min-avg': 'hjk, percentage',            
        }
    }
}

# intent: agg
# absolute
# type: what is ...
# The number of charging points in Berlin/Sachsen last month was 500(19% of the total in Germany). 
# The number of cars per charging points in Berlin/Sachsen last month was 500.
# The p_o_t of Berlin/Sachsen last month was 12%.
The {'increase' if increase else 'number'} of {kpi} in {place} {'' if DATE == 'now' else 'in'} {DATE} {'is' if DATE == 'now' else 'was'} "+str(round(result[0]))+ f"(round(100*result_1[0]/result_2[0], 2)% of the {'increase' if increase else 'total'} in Germany)"+"."
The {'increase of' if increase else ''} {kpi} in {place} {'' if DATE == 'now' else 'in'} {DATE} {'is' if DATE == 'now' else 'was'} "+str(round(result[0],1))+'%'+"."

# type: which county/state/county in state ...
# berlin had the highest/lowest number of charging points last month, which was 200(10% of the total in Germany)
# sachsen had the highest/lowest number of p_o_t last month, which was 10%
{place} had the {max if max else ''}{min if min else ''} {'increase' if increase else 'number'} of {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which {'is' if DATE == 'now' else 'was'}"+str(round(result[0]))+ f"(100*round(result_1[0]/result_2[0], 2)% of the {'increase' if increase else 'total'} in Germany)"+"."
{place} had the {max if max else ''}{min if min else ''} {'increase of' if increase else ''} {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which {'is' if DATE == 'now' else 'was'}"+str(round(result[0],1))+'%'+"."
# a in Hessen have most/least increase of chargingpoints last month, which was 20(1% of the total increase in Germany).
{place[0]} in {place[1]} had the {max if max else ''}{min if min else ''} {'increase' if increase else 'number'} of {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which {'is' if DATE == 'now' else 'was'}"+str(round(result[0]))+ f"(round(result_1[0]/result_2[0], 2)% of the total increase in Germany)"+"."
{place[0]} in {place[1]} had the {max if max else ''}{min if min else ''} {'increase of' if increase else ''}  {kpi} {'' if DATE == 'now' else 'in'} {DATE}, which {'is' if DATE == 'now' else 'was'}"+str(round(result[0],1))+'%'+"."




# type: what is/how large/how high the average
# The average number of charging points of a federal state/county last month is 500.
# The average number of charging points of all counties in Hessen is 500.
# The average p_o_t of a federal state/county last month is 5%.
The {avg} {'increase' if increase else 'number'} of {kpi} of a  {'state' if state else 'county'} {'' if DATE == 'now' else 'in'} {DATE} {'is' if DATE == 'now' else 'was'}+str(round(result[0])+"."
The {avg} {'increase' if increase else 'number'} of {kpi} of {place[0]} in {place[1]} {'' if DATE == 'now' else 'in'} {DATE} {'is' if DATE == 'now' else 'was'}+str(round(result[0])+"."
The {avg} {'increase of' if increase else ''} {kpi} of a  {'state' if state else 'county'} {'' if DATE == 'now' else 'in'} {DATE} {'is' if DATE == 'now' else 'was'}+str(round(result[0],1)+'%'+"."

# type: did berlin have 


# type: when did Berlin have ....




# intent: group
# absolute
res = ""
res += f"{result[1]}, {round(result[0]) if kpi != 'Percentage of target' else round(result[0],1)}{'%' if kpi == 'Percentage of target' else ''}  \n"

# increase



# intent: filter
# absolute
# increase
# yes-no
Yes, number of chargingpoints in sachsen from 2020 to 2022 was more than 500





# The increase of charging points in Hessen, Niedersachsen and Sachsen were 1(1%),2(2%),3(3%) between march 2019 and november 2021