class FuzzyExtractor(Component):
    name = "FuzzyExtractor"
    provides = ["entities"]
    requires = ["tokens"]
    defaults = {}
    language_list  ["en"]
    threshold = 90

    def __init__(self, component_config=None, *args):
        super(FuzzyExtractor, self).__init__(component_config)

    def train(self, training_data, cfg, **kwargs):
        pass

    def process(self, message, **kwargs):

        entities = list(message.get('entities'))

        # Get file path of lookup table in json format
        cur_path = os.path.dirname(__file__)
        if os.name == 'nt':
            partial_lookup_file_path = '..\\data\\lookup_master.json'
        else:
            partial_lookup_file_path = '../data/lookup_master.json'
        lookup_file_path = os.path.join(cur_path, partial_lookup_file_path)

        with open(lookup_file_path, 'r') as file:
            lookup_data = json.load(file)['data']

            tokens = message.get('tokens')

            for token in tokens:

                # STOP_WORDS is just a dictionary of stop words from NLTK
                if token.text not in STOP_WORDS:

                    fuzzy_results = process.extract(
                                             token.text, 
                                             lookup_data, 
                                             processor=lambda a: a['value'] 
                                                 if isinstance(a, dict) else a, 
                                             limit=10)

                    for result, confidence in fuzzy_results:
                        if confidence >= self.threshold:
                            entities.append({
                                "start": token.offset,
                                "end": token.end,
                                "value": token.text,
                                "fuzzy_value": result["value"],
                                "confidence": confidence,
                                "entity": result["entity"]
                            })

        file.close()

        message.set("entities", entities, add_to_output=True)