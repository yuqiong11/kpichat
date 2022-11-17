'''
Feature-based approach
1.1 Download a pre-trained BERT model.
1.2 Use BERT to turn natural language sentences into a vector representation.
1.3 Feed the pre-trained vector representations into a model for a downstream task (such as text classification).

Perform fine-tuning
2.1 Download a pre-trained BERT model.
2.2 Update the model weights on the downstream task.

If your dataset is not in English, it would be best if you use bert-base-multilingual-cased model. 
https://towardsdatascience.com/text-classification-with-bert-in-pytorch-887965e5820f  , https://github.com/ArmandDS/news_category/blob/master/News_Analysis_AO.ipynb
https://towardsdatascience.com/fine-tuning-bert-for-text-classification-54e7df642894  'Fine-Tuning BERT for Text Classification'
https://nyandwi.com/machine_learning_complete/35_using_pretrained_bert_for_text_classification/  'Using Pretrained BERT for Text Classification'
'''

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
# # import csv. data to pandas df
# df = pd.read_csv("./query_dataset_currently_used.csv", delimiter=";")
# # encode labels
# column_mapping = {
#     'ask-yes-or-no': 0,
#     'ask-provider': 1,
#     'ask-place': 2,
#     'ask-number': 3,
# }
# reversed_column_mapping = {
#     0: 'ask-yes-or-no',
#     1: 'ask-provider',
#     2: 'ask-place',
#     3: 'ask-number',
# }
# # df['Label'] = df['Label'].apply(lambda x: column_mapping[x])

# # split into trainingset, testset
# training_set, val_set = train_test_split(df, test_size=0.2, shuffle=True)
# X_train, y_train = training_set["Query"].tolist(), training_set["Label"].tolist()
# X_val, y_val = val_set["Query"].tolist(), val_set["Label"].tolist()


# print(y_val)
# # Load the BERT tokenizer
# tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
# # tokenize
# # pad to 100
# # training_encoded = tokenizer(X_train, return_tensors="pt", padding='max_length', max_length = 100)
# # val_encoded = tokenizer(X_val, return_tensors="pt", padding='max_length', max_length = 100)

# # create a dataset class to get data
# class QueryDataset(torch.utils.data.Dataset):
#     def __init__(self, texts, labels):
#         self.encodings = [tokenizer(text, return_tensors="pt", padding='max_length', max_length = 100) for text in texts]
#         self.labels = labels

#     def __getitem__(self, idx):
#         x = self.encodings[idx]
#         y = self.labels[idx]
#         return x, y

#     def __len__(self):
#         return len(self.labels)


# # create a model class
# class BertClassifier(nn.Module):

#     def __init__(self, dropout=0.5, path=None):

#         super(BertClassifier, self).__init__()
#         # import BERT-base pretrained model# import BERT-base pretrained model
#         if len(os.listdir(path)) != 0:
#             # load fine-tuned model
#             # config= BertConfig.from_pretrained("bert-base-cased")
#             self.bert = BertForSequenceClassification.from_pretrained(path)
#             # self.bert.load_state_dict(torch.load(path))
#         else:
#             # load pre-trained model
#             self.bert = BertForSequenceClassification.from_pretrained('bert-base-cased')
#         self.dropout = nn.Dropout(dropout)
#         # outputs = one of six labels
#         self.linear = nn.Linear(768, 6)
#         self.relu = nn.ReLU()

#     def forward(self, input_id, mask):

#         _, pooled_output = self.bert(input_ids=input_id, attention_mask=mask, return_dict=False)
#         dropout_output = self.dropout(pooled_output)
#         linear_output = self.linear(dropout_output)
#         final_layer = self.relu(linear_output)

#         return final_layer


# def train(model, X_train_data, X_val_data, y_train_data, y_val_data, learning_rate, epochs):

#     train_dataset = QueryDataset(X_train_data, y_train_data)
#     val_dataset = QueryDataset(X_val_data, y_val_data)

#     # load training data
#     train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)
#     val_loader = DataLoader(val_dataset, batch_size=2)

#     use_cuda = torch.cuda.is_available()
#     device = torch.device("cuda" if use_cuda else "cpu")

#     criterion = nn.CrossEntropyLoss()
#     optimizer = Adam(model.parameters(), lr= learning_rate)

#     if use_cuda:

#             model = model.cuda()
#             criterion = criterion.cuda()

#     for epoch_num in range(epochs):

#             total_acc_train = 0
#             total_loss_train = 0

#             for train_input, train_label in tqdm(train_loader):
#                 # print(train_input)
#                 # print(train_label)
#                 train_label = train_label.to(device)
#                 masks = train_input['attention_mask'].squeeze(1).to(device)
#                 ids = train_input['input_ids'].squeeze(1).to(device)
#                 # print(masks.size())
#                 # print(mask)
#                 # print(ids.size())
#                 # print(input_id)
#                 # print(train_label.size())
#                 output = model(input_ids=ids, attention_mask=masks, labels=train_label)
#                 loss = output[0]
#                 logits = output[1]
#                 # print(loss)
                
#                 total_loss_train += loss.item()
                
#                 # acc = (logits == train_label).sum().item()
#                 acc = (logits.argmax(dim=1) == train_label).sum().item()
#                 total_acc_train += acc

#                 model.zero_grad()
#                 loss.backward()
#                 optimizer.step()
            
#             total_acc_val = 0
#             total_loss_val = 0

#             with torch.no_grad():

#                 for val_input, val_label in val_loader:

#                     val_label = val_label.to(device)
#                     masks = val_input['attention_mask'].to(device)
#                     ids = val_input['input_ids'].squeeze(1).to(device)

#                     output = model(input_ids=ids, attention_mask=masks, labels=val_label)
#                     loss = output[0]
#                     logits = output[1]
#                     # batch_loss = criterion(output, val_label.long())
#                     total_loss_val += loss.item()
                    
#                     # acc = (logits == val_label).sum().item()
#                     acc = (logits.argmax(dim=1) == val_label).sum().item()
#                     total_acc_val += acc
            
#             print(
#                 f'Epochs: {epoch_num + 1} | Train Loss: {total_loss_train / len(y_train_data): .3f} \
#                 | Train Accuracy: {total_acc_train / len(y_train_data): .3f} \
#                 | Val Loss: {total_loss_val / len(y_val_data): .3f} \
#                 | Val Accuracy: {total_acc_val / len(y_val_data): .3f}')


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

#     print('Input Sentence: ', text)
#     print('Predicted Class: ', label)
#     return label
                  
# EPOCHS = 10
# LR = 1e-5
# PATH = "./bert_model"


# if len(os.listdir(PATH)) != 0:
#     # load fine-tuned model
#     # config= BertConfig.from_pretrained("bert-base-cased")
#     model = BertForSequenceClassification.from_pretrained(PATH, num_labels=2)
#     # self.bert.load_state_dict(torch.load(path))
#     print("loaded from local")
# else:
#     # load pre-trained model
#     model = BertForSequenceClassification.from_pretrained('bert-base-cased', num_labels=2)

# if __name__ == "__main__" : 
#     train(model, X_train, X_val, y_train, y_val, LR, EPOCHS)
#     print('training finished')
#     model.save_pretrained(PATH)
#     print('model saved')
