# import re
 
# test_str = "@charging_point / @area"

# pattern = '@([a-zA-Z0-9_]+)'
# params_list = re.findall(pattern, test_str)

# print(params_list)

# from rapidfuzz.process import extractOne, extract

# import pymongo

# myclient = pymongo.MongoClient("mongodb://localhost:27017/")
# mydb = myclient["emobility"]
# mycol = mydb["new_kpi_definition"]

# x = mycol.find_one({"kpi_name": "Chargers_per_square_kilometer"}, {"kpi_definition": 1})

# print(x)

# print(list('@my_param + @my_param_1/@param'))

'''
CRUD mongodb
'''

# import pymongo

# myclient = pymongo.MongoClient("mongodb://localhost:27017/")
# mydb = myclient["emobility"]
# mycol = mydb["new_kpi_definition"]

# mydict = [
#     # { "name": "hello", "place": "Berlin", "time":"May 2020"},
#     # { "name": "ooooo", "place": "Hamburg", "time":"May 2021"},
#     # { "name": "hello", "place": "Dresden", "time":"10.2019"},
#     # { "name": "ooooo", "place": "Stuttgart", "time":"June 2022"},
#     # { "name": "population", "place": "Dresden", "time":"10.2019"},
#     # { "name": "population", "place": "Berlin", "time":"June 2022"},
#     { "name": "ooooo", "place": "Sachsen", "time":"August 2021"},
#     { "name": "hello", "place": "Cottbus", "time":"202010"},
#     { "name": "ooooo", "place": "Bayern", "time":"March 2022"},
# ]

# mydict = [
#     { "name": "ooo", "entries": [[500, "Hamburg", "May 2020"]]},
# ]

# x = mycol.insert_many(mydict)
# for _ in mydict:
#     x = mycol.delete_many(_)

# delete all documents

# delete all documents which have 'null' as field value
# mycol.delete_many({'kpi_name': None})

'''
predict using BERT
'''
# import torch
# from transformers import BertForSequenceClassification, BertTokenizer

# model = BertForSequenceClassification.from_pretrained("./Query_classification/bert_model")
# tokenizer = BertTokenizer.from_pretrained('bert-base-cased')

# # text= "how many locations in Karlsruhe"
# text= "when will berlin reach 5000 chargingpoints"

# test_ids = []
# test_attention_mask = []

# # Apply the tokenizer
# sentence_encoded = tokenizer(text, return_tensors="pt", padding='max_length', max_length = 100)

# # Extract IDs and Attention Mask
# # test_ids.append(sentence_encoded['input_ids'])
# # test_attention_mask.append(sentence_encoded['attention_mask'])
# # test_ids = torch.cat(test_ids, dim = 0)
# # test_attention_mask = torch.cat(test_attention_mask, dim = 0)

# # Forward pass, calculate logit predictions
# with torch.no_grad():
#     output = model(input_ids = sentence_encoded['input_ids']).logits

# prediction = int(output.argmax(dim=1).cpu())

# print('Input Sentence: ', text)
# print('Predicted Class: ', prediction)


# kpi_name = "hello"
# with open('../lookup/New_KPI.txt', 'a') as f:
#     f.write(str(kpi_name)+'\n')



##############################################################
# from doctest import OutputChecker
# from posixpath import split
# import pandas as pd
# from sklearn.model_selection import train_test_split
# import numpy as np
# import torch
# import torch.nn as nn
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report
# import transformers
# from transformers import BertForSequenceClassification, BertTokenizer
# from torch.utils.data import DataLoader
# from torch.optim import Adam
# from tqdm import tqdm
# import os.path

# reversed_column_mapping = {
#     0: 'ask-yes-or-no',
#     1: 'ask-time',
#     2: 'ask-provider',
#     3: 'ask-place',
#     4: 'ask-number',
#     5: 'ask-charger-type'    
# }

# def predict(model, text, tokenizer):
#     use_cuda = torch.cuda.is_available()
#     device = torch.device("cuda" if use_cuda else "cpu")

#     # We need Token IDs and Attention Mask for inference on the new sentence
#     # test_ids = []
#     # test_attention_mask = []

#     # Apply the tokenizer
#     sentence_encoded = tokenizer(text, return_tensors="pt", padding='max_length', max_length = 100)

#     # Extract IDs and Attention Mask
#     # test_ids.append(sentence_encoded['input_ids'])
#     # test_attention_mask.append(sentence_encoded['attention_mask'])
#     # test_ids = torch.cat(test_ids, dim = 0)
#     # test_attention_mask = torch.cat(test_attention_mask, dim = 0)

#     # Forward pass, calculate logit predictions
#     with torch.no_grad():
#         output = model(input_ids = sentence_encoded['input_ids']).logits
#     prediction = int(output.argmax(dim=1).cpu())
#     # label = reversed_column_mapping[prediction]
#     label = prediction

    # print('Input Sentence: ', text)
    # print('Predicted Class: ', label)
    # print('output ', output)
    # return label

# PATH = "./Query_classification/bert_model"
# tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
# model = BertForSequenceClassification.from_pretrained(PATH, num_labels=2)
# text = "Was the locations in Hannover increased by 5 last year?"
# predict(model, text, tokenizer)


# my_text = "Which county had the most increase regarding charging stations last month?"
# print('state'in my_text or 'count' in my_text)

# import datetime
# print(datetime.date.today().month)


# import sys
# print(sys.path)


# s = "A:01 What is the date of the election ?"
# s = "kpi_name: charging_points_per_population"
# before,sep,after = s.partition(':') # could be, eg, a ':' instead
# print(before)
# print(after[1:])


# # Construction 1
# from spacy.tokenizer import Tokenizer
# from spacy.lang.en import English
# nlp = English()
# # Create a blank Tokenizer with just the English vocab
# tokenizer = Tokenizer(nlp.vocab)

# # Construction 2
# # from spacy.lang.en import English
# # nlp = English()
# # # Create a Tokenizer with the default settings for English
# # # including punctuation rules and exceptions
# # tokenizer = nlp.tokenizer
# text = "how many chargingpoints per square meter are there in Baden-Württemberg"
# tokens = tokenizer(text)
# print(tokens)


# Construction 1
# from spacy.tokenizer import Tokenizer
# from spacy.lang.en import English
# nlp = English()

# Creating a blank Tokenizer with just the English vocab
# tokenizer = Tokenizer(nlp.vocab)
# tokens = tokenizer("all federal states with Percentage_of_target more than 10% last month.")
# print("Blank tokenizer",end=" : ")
# for token in tokens:
#     print(token,end=', ')
 
# Construction 2
# from spacy.lang.en import English
# nlp = English()

# Creating a Tokenizer with the default settings for English
# tokenizer = nlp.tokenizer
# tokens = tokenizer("all federal states with Percentage_of_target more than 10% last month.")
# print("\nDefault tokenizer",end=' : ')
# for token in tokens:
#     print(token,end=', ')
a=1
text = '%' if True else ''
my_text = f"{a}"+str(round(2.3,1))+text
print(my_text)