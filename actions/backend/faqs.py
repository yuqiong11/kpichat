import pickle
import os.path
import time
from sentence_transformers import SentenceTransformer, util

query = "What are the advantages of choosing electric cars?"
ANSWERS = [
    "An electric vehicle (EV) is a vehicle that uses one or more electric motors for propulsion.", 
    "Electric mobility, according to the definition of the German government and the National Development Plan for Electric Mobility (NEP) comprises all street vehicles that are powered by an electric motor and primarily get their energy from the power grid, in other words: can be recharged externally.",
    "The history of the electric car started with British inventor Robert Anderson: He built his electrically powered vehicle in Aberdeen, a port city in northeast Scotland, between 1832 and 1839.",
    "Charging Infrastructure means the network of charging facilities for Electric Vehicles open to the public, including the Charging Stations and other associated hardware, and software",
    "China had more than 1.1 million publicly accessible electric vehicle chargers in 2021, accounting for over 65 percent of such chargers in the world. ",
    "EVs are inevitably safer than their conventional counterparts. With fewer moving components and the absence of flammable fuel, EVs are less prone to the common safety concerns of conventional vehicles.",
    "In over a year, just one electric car on the roads can save an average 1.5 million grams of CO2. That's the equivalent of four return flights from London to Barcelona.",
    "Electric vehicles have many benefits, including: Cleaner environment, Lower running costs, Less noise, faster acceleration etc.",
    "The Tesla Model Y has emerged as the most popular electric vehicle (EV) in Europe. In 2022, Tesla sold 137,052 Model Ys in Europe giving it significant headway against rival vehicles.",
    "The time it takes to charge an electric car can be as little as 30 minutes or more than 12 hours. This depends on the size of the battery and the speed of the charging point. For example, A typical electric car (60kWh battery) takes just under 8 hours to charge from empty-to-full with a 7kW charging point.",
    "According to current industry expectations, EV batteries are projected to last between 100,000 and 200,000 miles, or about 15 to 20 years."
    ]



class RetrieveAnswer():
    def __init__(self):

        # load the model
        self.model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')

        # Encode documents if needed
        if not os.path.isfile('./util/sentence_embeddings.pkl'):
            self.doc_emb = self.model.encode(ANSWERS)

        # save the list using pickle
        with open("sentence_embeddings.pkl", "wb") as f:
            pickle.dump(self.doc_emb, f)

        # load the saved list later
        with open("sentence_embeddings.pkl", "rb") as f:
            self.answers = pickle.load(f)

    def look_up(self, query):
        # encode query
        query_emb = self.model.encode(query)

        #Compute dot score between query and all document embeddings
        scores = util.dot_score(query_emb, self.doc_emb)[0].cpu().tolist()

        #Combine docs & scores
        doc_score_pairs = list(zip(ANSWERS, scores))

        #Sort by decreasing score
        doc_score_pairs = sorted(doc_score_pairs, key=lambda x: x[1], reverse=True)

        #Output passages & scores
        for doc, score in doc_score_pairs:
            if score >= 0.4:
                return doc
            break


# start_retrieve = retrieveAnswer()
# print(start_retrieve.look_up(query))s