# import datetime 
# tod = datetime.datetime.now()
# print(tod.month)
# d = datetime.timedelta(days = 120)
# a = tod - d
# print('0'+str(a.month))

# a=['hello', 'hi']
# b='hello'
# print(b in a)


# s1='end of 2020'
# s2='2020'
# s3=None
# if s2 in None:
#     print('good')

# abc = ["apple", "banana", "cherry"]

# for e in abc:
#   print(e)
#   if e == 'banana':
#     print('heeee')
#     break

# # print('got it')

# fruits = ["apple", "banana", "cherry"]
# for x in fruits:
#   print(x)
#   if x == "banana":
#     print('hiiii')
#     break
'''
a='hi'
if a in ['hello', 'hi']:
  print('it is a greeting')'''

# print(round(8))

# print("hello hi" in "huhu hello hi")
# print("hello hi hi".split()[-1])
# print(len("hello hi hi".split()))


# string1 = '''Welcome
# to my
# pythonexamples.org'''

# #split string by single space
# chunks = string1.split('\n')

# print(chunks)

# from flashtext import KeywordProcessor
# keyword_processor = KeywordProcessor()
# # keyword_processor.add_keyword(<unclean name>, <standardised name>)
# keyword_processor.add_keyword('Berlin')
# keyword_processor.add_keyword('Dresden')
# keyword_processor.add_keyword('Emsland')
# keyword_processor.add_keyword('Leipzig')
# keywords_found = keyword_processor.extract_keywords('show the locations in Emsland.')
# print(keywords_found)

# with open('./csvData.csv', 'r', encoding='utf8') as f:
#     data = f.read()
#     places = data.split('\n')

my_d = {'a': 1, 'b': 2}

# print(my_d.get('a', 'a'))
# print(my_d.a)

from xmlrpc.client import boolean
from thefuzz import process

with open('GPE_any.txt', 'r', encoding='utf8') as f:
    data = f.read()
    places = data.split('\n')

# for word in "What is the number of charging points in Berlin in December 2021?":
#   result, score = process.extractOne(word, places)
#   print(word)
#   print(result)
#   print(score)

# print(places)   
# choices = ["Stuttgart", "Germany", "New York Giants", "Dallas Cowboys", "Zwickau","Berlin"]

# result1 = process.extractOne("Berlinn", choices)
# print(result)
# print(score)
# print(result1)

# result1 = process.extractOne("know", places)
# result2 = process.extractOne("what", places)

# print(result1)
# print(result2)

# import spacy
# #loading the english language small model of spacy
# en = spacy.load('en_core_web_md')
# stopwords = en.Defaults.stop_words

# print('I' in stopwords)

# import nltk
# from nltk.corpus import stopwords
# nltk.download('stopword')

# print('Hl'.lower())

# text = "Spread love everywhere you go. Let no one ever come to you without leaving happier"
# en_stopwords = stopwords.words('english')
# print(len(en_stopwords))

# import sys
# # adding target folder to the system path
# path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
# sys.path.insert(0, path)
# from time_mapping import mapped_time


import torch
# a = torch.zeros(10)
b = torch.rand(10)
# print(b.dim())
# print(a+b)


# my_list = ['a', 'b', 'c','d']
# print(set(my_list))

# from transformers import BertTokenizer, BertModel
# tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
# # model = BertModel.from_pretrained("bert-base-uncased")
# text = "Replace me by any text you'd like."
# encoded_input = tokenizer(text, return_tensors='pt')
# # output = model(**encoded_input)
# print(encoded_input)

# from sentence_transformers import SentenceTransformer, util
# model = SentenceTransformer('all-MiniLM-L6-v2')

# Two lists of sentences
# sentences1 = ['The cat sits outside',
#              'A man is playing guitar',
#              'The new movie is awesome']

# sentences2 = ['The dog plays in the garden',
#               'A woman watches TV',
#               'The new movie is so great']

# query = 'in {mapped_time}, show me the smallest number of {kpi} in {place}?'
# query = 'Give me the least number of {kpi} of a county in {mapped_time}'

# sql_templates = [
#     'SELECT SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
#     'SELECT MAX({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
#     'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
#     'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
#     'SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
#     'SELECT {kpi} FROM \"E-Mobility\".emo_historical WHERE state={place};',
#     'SELECT SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
#     'SELECT MAX({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
#     'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
#     'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
#     'SELECT {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';'
# ]



# removal_list = ['SELECT', 'FROM', '\"E-Mobility\".emo_historical']

# def preprocess_templates(tems, removal_list):
#     for i in range(len(tems)):
#         for word in removal_list:
#             tems[i] = tems[i].replace(word, "")

#     return tems

# preprocessed_templates = preprocess_templates(sql_templates, removal_list)

#Compute embedding for both lists

#For query, special infos e.g. location level should be added, which is optional.
# Locations levels: Germany, federal state, county, general federal state, general county
# loc_vec = 
# encoded_query = model.encode(query, convert_to_tensor=True) * len(sql_templates)
# print('query size', encoded_query.size())

# # special infos must be reflected as well
# encoded_templates = model.encode(preprocessed_templates, convert_to_tensor=True)
# print('templates size', encoded_templates.size())
# #Compute cosine-similarits
# cosine_scores = util.cos_sim(encoded_query, encoded_templates)
# print(cosine_scores)
# #Output the pairs with their score
# for i in range(len(sql_templates)):
#     print("{} \t\t Score: {:.4f}".format(sql_templates[i], cosine_scores[0][i]))


# import torch

# test_query = 'I want to know the lowest number of [kpi] in [place_state] in [mapped_time]'
# test_tems = [
#                     'I am interested in min number of [kpi] in [mapped_time] in [place_state]','Give the smallest [kpi] number of [place_state] in [mapped_time].',
#                     'I want to know the avg number of [kpi] in [place_state] in [mapped_time]','In [place_state], what is the mean number of [kpi] in [mapped_time]',
#                     'return number of [kpi] of in [place_county] in [mapped_time]', 'in [mapped_time], what is the number of [kpi] of [place_county]', 
#                     'what is the average number of [kpi] of a federal state in [mapped_time]','how many [kpi] on average does a state have at [mapped_time]?'
#             ]
# test_tems_6 = [
#     'I am interested in min number of [kpi] in [mapped_time] in [place_state]','Give the smallest [kpi] number of [place_state] in [mapped_time].'
# ]
# test_tems_7 = [
#     'I want to know the avg number of [kpi] in [place_state] in [mapped_time]','In [place_state], what is the mean number of [kpi] in [mapped_time]'
# ]
# test_tems_8 = [
#     'return number of [kpi] of in [place_county] in [mapped_time]', 'in [mapped_time], what is the number of [kpi] of [place_county]'
# ]
# test_tems_9 = [
#     'what is the average number of [kpi] of a federal state in [mapped_time]','how many [kpi] on average does a state have at [mapped_time]?'
# ]

# keyword_6 = ['min']
# keyword_7 = ['avg']
# keyword_8 = ['place_county']
# keyword_9 = ['average']
# keyword_10 = ['place_state']
# keyword_11 = ['state']
# keyword_12 = ['lowest']

# encoded_k_6 = model.encode(keyword_6, convert_to_tensor=True)
# encoded_k_7 = model.encode(keyword_7, convert_to_tensor=True)
# encoded_k_8 = model.encode(keyword_8, convert_to_tensor=True)
# encoded_k_9 = model.encode(keyword_9, convert_to_tensor=True)
# encoded_k_10 = model.encode(keyword_8, convert_to_tensor=True)
# encoded_k_11 = model.encode(keyword_9, convert_to_tensor=True)
# encoded_k_12 = model.encode(keyword_8, convert_to_tensor=True)

# encoded_query = model.encode(test_query, convert_to_tensor=True) + torch.mean(torch.stack((encoded_k_10, encoded_k_11, encoded_k_12)), dim=0)
# encoded_query = model.encode(test_query, convert_to_tensor=True) + encoded_k_10 + encoded_k_11 + encoded_k_12
# encoded_query = model.encode(test_query, convert_to_tensor=True) + encoded_k_6
# encoded_query = model.encode(test_query, convert_to_tensor=True)
# encoded_templates = model.encode(test_tems, convert_to_tensor=True)
# encoded_templates_6 = torch.mean(model.encode(test_tems_6, convert_to_tensor=True), dim=0) + torch.mean(torch.stack((encoded_k_6, encoded_k_8, encoded_k_9)), dim=0)
# encoded_templates_7 = torch.mean(model.encode(test_tems_7, convert_to_tensor=True), dim=0) + torch.mean(torch.stack((encoded_k_7, encoded_k_8, encoded_k_9)), dim=0)
# encoded_templates_6 = torch.mean(model.encode(test_tems_6, convert_to_tensor=True), dim=0) + encoded_k_6 + encoded_k_10
# encoded_templates_7 = torch.mean(model.encode(test_tems_7, convert_to_tensor=True), dim=0) + encoded_k_7 + encoded_k_10
# encoded_templates_6 = torch.mean(model.encode(test_tems_6, convert_to_tensor=True), dim=0) + encoded_k_6
# encoded_templates_7 = torch.mean(model.encode(test_tems_7, convert_to_tensor=True), dim=0) + encoded_k_7
# encoded_templates_6 = torch.mean(model.encode(test_tems_6, convert_to_tensor=True), dim=0)
# encoded_templates_7 = torch.mean(model.encode(test_tems_7, convert_to_tensor=True), dim=0)
# encoded_templates_8 = torch.mean(model.encode(test_tems_8, convert_to_tensor=True), dim=0)
# encoded_templates_9 = torch.mean(model.encode(test_tems_9, convert_to_tensor=True), dim=0) 
# print('encoded_template_6', .mean())
# print('encoded_template_7', encoded_templates_7)
# print('encoded_template_8', encoded_templates_8)
# print('encoded_template_9', encoded_templates_9)
# cosine_scores_6 = util.cos_sim(encoded_query, encoded_templates_6)
# print('cosine_scores_6', cosine_scores_6)
# cosine_scores_7 = util.cos_sim(encoded_query, encoded_templates_7)
# print('cosine_scores_7', cosine_scores_7)
# cosine_scores_8 = util.cos_sim(encoded_query, encoded_templates_8)
# print('cosine_scores_8', cosine_scores_8)
# cosine_scores_9 = util.cos_sim(encoded_query, encoded_templates_9)
# print('cosine_scores_9', cosine_scores_9)


# print([] is None)
def change_letter(input_str, mask, start, end): 
    return input_str[:start] + mask + input_str[end+1:]

# test = "hi how are you what's that".split()

# print(test)

# print('hi how are you'[3:5])

# my_dict = {'a': 1, 'b': 2}
# print('a' in my_dict)


import json 

def load_query_clusters(path):
    with open(path, "r") as clusters_file:
        query_clusters = json.load(clusters_file)
    return query_clusters


def add_new_data(path, new_data, intent, cluster_name, clusters):
    clusters[intent][cluster_name].append(new_data)
    with open(path, 'w') as clusters_file:
        clusters_file.write(json.dumps(clusters))


# clusters=load_query_clusters('test.txt')
# add_new_data('test.txt', 'hiiii', 'agg_query', 'cluster0', clusters)


# print(len({'a':1, 'b':2}))
# print('202202' > '202203')

# for _ in "hello, where are you":
#     print(_)

# print("hello, where are, you".split(","))
# import psycopg2
# conn = psycopg2.connect("host=81.169.137.234 dbname=workbench user=david.reyer password=start_david")
# cur = conn.cursor()
# q = f"SELECT no_total_locations FROM \"E-Mobility\".emo_historical WHERE month=202001 AND county LIKE '%Amberg%';"
# cur.execute(q)
# results = cur.fetchall()
# for result in results:
#     print(f"result[0], result[1]")
print("state" in "states")

# print(boolean(None))