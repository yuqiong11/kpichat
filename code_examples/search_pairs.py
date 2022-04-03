from numpy import empty
from sentence_transformers import SentenceTransformer, util
from statistics import mean
from sklearn import cluster
import torch



#'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};'
query_cluster_0 = [
    'Give me the least number of {kpi} of a county in {mapped_time}',
    'lowest number of {kpi} of all counties at {mapped_time}'
]

#'SELECT {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';'
query_cluster_1 = [
    'return number of {kpi} of in {place} in {mapped_time}',
    'in {mapped_time}, what is the number of {kpi} of {place}'
]

#'SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};'
query_cluster_2 = [
    'what is the average number of {kpi} of a federal state in {mapped_time}',
    'how many {kpi} on average does a state have at {mapped_time}?'
]

#'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};'
query_cluster_3 = [
    'I want to know the avg number of {kpi} in {place} in {mapped_time}',
    'In {place}, what\s the mean number of {kpi} in {mapped_time}'
]

query_clusters = {'a':query_cluster_0, 'b':query_cluster_1, 'c':query_cluster_2, 'd':query_cluster_3}

sql_mapping = {
    'cluster0': 'SELECT SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster1': 'SELECT MAX({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};', 
    'cluster2': 'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster3': 'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};',
    'cluster4': 'SELECT SUM({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
    'cluster5': 'SELECT MAX({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
    'cluster6': 'SELECT MIN({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
    'cluster7': 'SELECT AVG({kpi}) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND state={place};',
    'cluster8': 'SELECT {kpi} FROM \"E-Mobility\".emo_historical WHERE month={mapped_time} AND county LIKE \'%{place}%\';',  
    'cluster9': 'SELECT SUM({kpi})/COUNT(DISTINCT(state)) FROM \"E-Mobility\".emo_historical WHERE month={mapped_time};'            
}



model = SentenceTransformer('all-MiniLM-L6-v2')

class SentenceEncoding:

    def __init__(self, clusters, model):
        self.clusters = clusters
        self.model = model
    
    def encoding(self, query):
        encoded_query = self.model.encode(query, convert_to_tensor=True)       
        return encoded_query

    @staticmethod
    def dict_to_list(dict):
        return list(dict.values())

    def process(self):
        clusters = self.dict_to_list(self.clusters)
        processed_query = map(self.encoding, clusters)
        return processed_query

    def cal_centroid(self):
        clusters = self.process()
        cluster_centroids = []
        for cluster in clusters:           
            centroid = torch.mean(cluster, dim=0)
            cluster_centroids.append(centroid)

        return torch.stack(cluster_centroids)

sen_encoding = SentenceEncoding(query_clusters, model)


processed_clusters = sen_encoding.cal_centroid()

# new_query = 'tell me number of {kpi} in {place} in {mapped_time}'
new_query = 'tell me the average number of {kpi} of all states in Germany in {mapped_time}'

processed_query = sen_encoding.encoding(new_query)


cosine_scores = util.cos_sim(processed_query*len(processed_clusters), processed_clusters)

# display the results
for i in range(len(processed_clusters)):
    print(len(processed_clusters[i]))
    print("{} \t\t Cluster{} \t\t Score: {:.4f}".format(new_query, i, cosine_scores[0][i]))

# get the highest score and the cluster
highest_score, idx = torch.max(cosine_scores, dim=1)
highest_score = float(highest_score)
idx = int(idx)
cluster_name = 'cluster' + str(idx)

print(f"highest score: {highest_score}, cluster: {cluster_name}")

def output_template(cluster, mapping):
    return mapping[cluster]

print(output_template(cluster_name, sql_mapping))



# words matrix  
# avg, min, max, total
keywords_mat = torch.zeros(10, len(processed_clusters[0]))
for i in range(10):
    keywords_mat[i][i] = 0.5

print(keywords_mat)
