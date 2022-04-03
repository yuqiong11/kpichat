from os import X_OK
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
corpus = [
            'What\'s the total number of [kpi] in Germany in [mapped_time]? Tell me in Germany, how many [kpi] are there in [mapped_time]?',
            'What\'s the largest number of [kpi] of a county in [mapped_time]? The highest number of [kpi] of all counties in [mapped_time]',
            'What\'s the lowest number of [kpi] of a county in [mapped_time] Give me the least number of [kpi] of a county in [mapped_time]',
            'The average number of [kpi] [mapped_time] of county. how many [kpi] on average does a county have?',
            'How many [kpi] are there in [place_state] [mapped_time]? In [mapped_time], What\'s the number of [kpi] in [place_state]?',
            'What\'s the largest number of [kpi] of a county in [place_state] in [mapped_time]? I want to know the bigest number of [kpi] of a county in [place_state] in [mapped_time]',
            'I am interested in min number of [kpi] in [mapped_time] in [place_state] Give the samallest [kpi] number of [place_state] in [mapped_time].',
            'I want to know the avg number of [kpi] in [place_state] in [mapped_time] In [place_state], what is the mean number of [kpi] in [mapped_time]',
            'return number of [kpi] of in [place_county] in [mapped_time] in [mapped_time], what is the number of [kpi] of [place_county]',
            'what is the average number of [kpi] of a federal state in [mapped_time] how many [kpi] on average does a state have at [mapped_time]?'
]

# keywords = ['avg', 'average', 'mean', 'max', 'min', 'largest', ']
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(corpus)
# print(X)
df = pd.DataFrame(X.toarray(), columns = vectorizer.get_feature_names())
print(df)
word_score = dict(zip(vectorizer.get_feature_names(), X.toarray()[0]))
print(word_score)
word_score_1 = dict(zip(vectorizer.get_feature_names(), X.toarray()[1]))
print(word_score_1)

keywords_mat = torch.zeros(10, len(processed_clusters[0]))
for i in range(10):
    keywords_mat[i][i] = 0.5

print(keywords_mat)