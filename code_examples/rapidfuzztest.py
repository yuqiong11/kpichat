from rapidfuzz.process import extractOne, extract
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity
from rapidfuzz.fuzz import ratio

choices = ["Atlanta Falcons", "Berlin", "New York Giants", "Dallas Cowboys"]
# print(extractOne("berliin", choices, scorer=jaro_winkler_similarity))

# print(normalized_levenshtein("Berlin", "Berliin"))
# print(normalized_levenshtein("Berlin", "berlin"))
print(extract('Stuttgart', ['hi'], scorer=jaro_winkler_similarity, score_cutoff=80))