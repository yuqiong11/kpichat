CLUSTERS_SQL_MAPPING = {
    "agg_query": 
    {
    'cluster0': 'SELECT SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster1': 'SELECT MAX({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};', 
    'cluster2': 'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster3': 'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster4': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';',
    'cluster5': 'SELECT MAX({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';',
    'cluster6': 'SELECT MIN({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';',
    'cluster7': 'SELECT AVG({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state=\'{place}\';',
    'cluster8': 'SELECT {kpi}, county FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';',  
    'cluster9': 'SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};'            
    },
    "group_sort_query":
    {
    'cluster0': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state;',
    'cluster1': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC;', 
    'cluster2': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum ASC;',         
    },
    "filter_query":
    {
    'cluster0': 'SELECT county, {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi} > (SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});',
    'cluster1': 'SELECT county, {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi} < (SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});', 
    'cluster2': 'SELECT county, {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi} > {number_l} AND {kpi} < {number_r};',
    'cluster3': 'SELECT county, {kpi}} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND {kpi} {symbol} {number};',
    'cluster4': 'SELECT state, SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi}) > (SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});',
    'cluster5': 'SELECT state, SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi}) < (SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time});',
    'cluster6': 'SELECT state, SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi}) > {number_l} AND SUM({kpi}) < {number_r};',
    'cluster7': 'SELECT state, SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state HAVING SUM({kpi}) {symbol} {number}};',           
    },
    "limit_query":
    {
    'cluster0': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum DESC Limit {CARDINAL};',
    'cluster1': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} GROUP BY state ORDER BY sum Limit {CARDINAL};'       
    },
    "window_query":
    {
    'cluster0': 'SELECT SUM({kpi}), state FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state IN {place} GROUP BY state;'     
    }
}


import json 

def load_query_clusters(path):
    with open(path, "r") as clusters_file:
        query_clusters = json.load(clusters_file)
    return query_clusters


def add_new_data(path, new_data, intent, cluster_name):
    clusters = load_query_clusters(path)
    clusters[intent][cluster_name].append(new_data)
    with open(path, 'w') as clusters_file:
        clusters_file.write(json.dumps(clusters))

    print('closed')





QUERY_CLUSTERS = {
    "agg_query":
    {
        'cluster0':
        [
            'What\'s the total number of [kpi] in Germany in [mapped_time]?',
            'Tell me in Germany, how many [kpi] are there in [mapped_time]?'
        ],       
        'cluster1':
        [
            'What\'s the largest number of [kpi] of a county in [mapped_time]?',
            'The highest number of [kpi] of all counties in [mapped_time]'
        ],
        'cluster2':
        [
            'What\'s the lowest number of [kpi] of a county in [mapped_time]',
            'Give me the least number of [kpi] of a county in [mapped_time]'
        ],
        'cluster3':
        [
            'What is the average number of [kpi] of county in [mapped_time].',
            'how many [kpi] on average does a county have in [mapped_time]?'
        ],
        'cluster4':
        [
            'How many [kpi] are there in [place_state] [mapped_time]?',
            'In [mapped_time], What\'s the number of [kpi] in [place_state]?'
        ],
        'cluster5':
        [
            'What\'s the largest number of [kpi] of a county in [place_state] in [mapped_time]?',
            'I want to know the bigest number of [kpi] in [place_state] in [mapped_time]'
        ],
        'cluster6':
        [
            'I am interested in min number of [kpi] in [mapped_time] in [place_state]',
            'Give the smallest [kpi] number of [place_state] in [mapped_time].'
        ],
        'cluster7':                 
        [
            'I want to know the avg number of [kpi] in [place_state] in [mapped_time]',
            'In [place_state], what is the mean number of [kpi] in [mapped_time]'
        ],
        'cluster8':
        [
            'return number of [kpi] of in [place_county] in [mapped_time]',
            'in [mapped_time], what is the number of [kpi] of [place_county]'
        ],
        'cluster9':
        [
            'what is the average number of [kpi] of a federal state in [mapped_time]',
            'how many [kpi] on average does a state have in [mapped_time]?'
        ]
    },
    "group_sort_query":
    {
        'cluster0':
        [
            'Give a overview of number of [kpi] in each federal state [mapped_time].',
            'number of [locations]{"entity": "kpi", "value": "Locations"} group by [federal state](place) in [mapped_time].'
        ],
        'cluster1':
        [
            'descend',
            'Order [kpi] for each state descending.',
            'Give a desc order of number of [kpi] of federal state in [mapped_time].'
        ],
        'cluster2':
        [
            'ascend',
            'Show number of [kpi] in each federal state by ascending order [mapped_time].',
            'Return a ascending order of number of [kpi] in each federal state in [mapped_time].'
        ]
    },
    "filter_query":
    {
        'cluster0':
        [
            'Give me all counties that have [kpi] above average in [mapped_time].',
            'show all county which have over average [kpi] in [mapped_time].'
        ],
        'cluster1':
        [
            'In [mapped_time], give me counties that have [kpi] below average in [mapped_time].',
            'show all counties which have under average [kpi] in [mapped_time].'
        ],
        'cluster2':
        [
            'show all counties that have between [number_l]-[number_r] [kpi] [mapped_time].',
            'which counties have [number_l]-[number_r] number of [kpi] in [mapped_time]?'
        ],
        'cluster3':
        [
            'show all counties that have [le] [kpi] in [mapped_time].',
            'Give me counties whose number of [kpi] is [ge] [mapped_time].'
        ],
        'cluster4':
        [
            'Give me all states that have [kpi] above average in [mapped_time].',
            'show states which have over average [kpi] in [mapped_time].'
        ],
        'cluster5':
        [
            'In [mapped_time], give me states that have [kpi] below average in [mapped_time].',
            'show all states which have under average [kpi] in [mapped_time].'    
        ],
        'cluster6':
        [
            'states',
            'above average',
            'Give me all states that have [kpi] more than average in [mapped_time].',
            'Give me all states that have [kpi] above average in [mapped_time].'
        ],
        'cluster7':
        [
            '[le]',
            '[ge]',
            'states',
            'Return federal states that have [le] [kpi] in [mapped_time].',
            'show me the states that have [ge] [kpi] in [mapped_time].'
        ]

    },
    "limit_query":
    {
        'cluster0':
        [
            'top',
            'Return the top [CARDINAL] states that has the most [kpi] in [mapped_time].',
            'Give me [CARDINAL] states on top in [mapped_time].'
        ],
        'cluster1':
        [
            'last',
            'the [CARDINAL] states that has the lowest [kpi] in [mapped_time].',
            'show the below [CARDINAL states that has the most [kpi] in [mapped_time].'
        ]
    },
    "window_query":
    {
        'cluster0':
        [
            '[place_state_list]',
            'What\'s the number of [kpi] in [place_state_list] in [mapped_time]?',
            'list [kpi] in [place_state_list] in [mapped_time]?'
        ]
    }
}

# with open('query_clusters.txt', 'w') as clusters_file:
#     clusters_file.write(json.dumps(QUERY_CLUSTERS))
    


 
     


