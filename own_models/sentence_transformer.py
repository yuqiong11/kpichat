from ctypes.wintypes import BOOLEAN
from numpy import empty
from sentence_transformers import SentenceTransformer, util
from statistics import mean
from sklearn import cluster
import torch

import os.path

import sys
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/mappings'
sys.path.insert(0, path)

from sql_mapping import CLUSTERS_SQL_MAPPING, QUERY_CLUSTERS


model = SentenceTransformer('all-MiniLM-L6-v2')

# Parameters
DEFAULT_PARAMS = {
    'model': model,
    'query_clusters': QUERY_CLUSTERS,
    'mapping': CLUSTERS_SQL_MAPPING,
    'path': "./own_models/centroids.pt",
    'load_centroids': True
}



class SentenceEncoding():
    def __init__(self, model):
        self.model = model

    def encoding(self, query):
        encoded_query = self.model.encode(query, convert_to_tensor=True)       
        return encoded_query
    

class ClusterEncoding(SentenceEncoding):

    def __init__(self, clusters, model, intent):
        self.clusters = clusters
        self.model = model
        self.intent = intent


    @staticmethod
    def dict_to_list(dict):
        return list(dict.values())


    def encoded(self):
        clusters = self.dict_to_list(self.clusters[self.intent])
        results = map(self.encoding, clusters)
        return results


    def cal_centroid(self):
        clusters = self.encoded()
        cluster_centroids = []
        for cluster in clusters:           
            centroid = torch.mean(cluster, dim=0)
            cluster_centroids.append(centroid)

        return torch.stack(cluster_centroids)

    def save(self, path):
        centroids = self.cal_centroid()
        torch.save(centroids, path)


def sentence_encoding(model, query):
    encoded_query = SentenceEncoding(model).encoding(query)
    return encoded_query


def cluster_encoding(clusters, model, intent, path):
    ClusterEncoding(clusters, model, intent).save(path)

    

def output_template(query, intent, query_clusters, mapping, path, model, load_centroids):

    # encoding
    if os.path.exists(path) and load_centroids:
        print('#########################load')
        centroids = torch.load(path)
    else:
        cluster_encoding(query_clusters, model, intent, path)
        centroids = torch.load(path)
    encoded_query = sentence_encoding(model, query)
    # calculating similarity
    cosine_scores = util.cos_sim(encoded_query*len(centroids), centroids)
    # get the highest score and the cluster
    highest_score, idx = torch.max(cosine_scores, dim=1)
    highest_score = float(highest_score)
    idx = int(idx)
    cluster_name = 'cluster' + str(idx)

    return mapping[intent][cluster_name]

# test
new_query = 'The lowest number of [kpi] in [place_state] in [DATE]?'
print(output_template(new_query, "agg_query", QUERY_CLUSTERS, CLUSTERS_SQL_MAPPING, "./own_models/centroids.pt", model,  load_centroids=True))




# The lowest number of locations of in Sachsen in Feb 2020?

























# class SentenceEncoding:

#     def __init__(self, clusters, model, intent):
#         self.clusters = clusters
#         self.model = model
#         self.intent = intent


#     def encoding(self, query):
#         encoded_query = self.model.encode(query, convert_to_tensor=True)       
#         return encoded_query

#     @staticmethod
#     def dict_to_list(dict):
#         return list(dict.values())

#     @staticmethod
#     def retrieve_dict_values(dict, key):
#         '''return a list'''
#         return [v[key] for k,v in dict.items()]


#     def encoded(self, key):
#         # clusters = self.dict_to_list(self.clusters[self.intent])
#         values = self.retrieve_dict_values(self.clusters[self.intent], key)
#         results = map(self.encoding, values)
#         return results

#     def get_all_keywords(self):
#         all_keywords = []
#         for v in self.clusters[self.intent].values():
#             for k in v['keywords']:
#                 all_keywords.append(k)
#         return all_keywords

#     def cal_centroid(self, clusters=None, keywords=None):
#         if clusters == None:
#             clusters_ = self.encoded('queries')
#         if keywords == None:
#             keywords_ = self.encoded('keywords')

#         centroids = []

#         if clusters == None:
#             for cluster in clusters_:       
#                 centroid = torch.mean(cluster, dim=0)
#                 for keyword_per_cluster in keywords_:
#                     for keyword in keyword_per_cluster:
#                         centroid = centroid + keyword
#                     centroids.append(centroid)
#         else:
#             for keyword in keywords:
#                 centroid = clusters + keyword            
#             centroids.append(centroid)
#         return torch.stack(centroids)


# def extract_keywords(new_query, keywords_list):
#     return [k for k in keywords_list if k in new_query]

# sen_encoding = SentenceEncoding(query_clusters, model, intent="agg_query")
# centroids = sen_encoding.cal_centroid()

# # new_query = 'tell me number of {kpi} in {place} in {mapped_time}'
# # new_query = 'tell me the average number of {kpi} of all states in Germany in {mapped_time}'
# # new_query = 'I want to know the lowest number of [kpi] of a county in [place_state] in [mapped_time]'
# new_query = 'I want to know the lowest number of [kpi] in [place_state] in [mapped_time]'

# def output_template(query, mapping, centroids, intent):
#     # number
#     encoded_query = sen_encoding.encoding(query)
#     # str
#     all_keywords = sen_encoding.get_all_keywords()
#     print('all_keywords ', all_keywords)
#     # str
#     query_keywords = list(set(extract_keywords(query, all_keywords)))
#     print('extracted_keywords ', query_keywords)
#     #number 
#     encoded_query_keywords = sen_encoding.encoding(query_keywords)
#     query_keyword_added = sen_encoding.cal_centroid(clusters=encoded_query, keywords=encoded_query_keywords)
#     cosine_scores = util.cos_sim(query_keyword_added*len(centroids), centroids)

#     # get the highest score and the cluster
#     highest_score, idx = torch.max(cosine_scores, dim=1)
#     highest_score = float(highest_score)
#     idx = int(idx)
#     cluster_name = 'cluster' + str(idx)
#     print(cluster_name)

#     # display the results
#     for i in range(len(centroids)):
#         print("{} \t\t Cluster{} \t\t Score: {:.4f}".format(new_query, i, cosine_scores[0][i]))

#     return mapping[intent][cluster_name]

# print(output_template(new_query, cluster_sql_mapping, centroids, intent="agg_query"))