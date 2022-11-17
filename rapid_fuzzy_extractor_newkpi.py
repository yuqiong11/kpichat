from typing import Dict, Text, Any, List, Type
# from cv2 import threshold

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.constants import ENTITIES, TEXT_TOKENS, TEXT
from rasa.nlu.constants import TOKENS_NAMES 
from rasa.nlu.utils.spacy_utils import SpacyModel, SpacyNLP
from rasa.nlu.tokenizers.tokenizer import Tokenizer

from rapidfuzz.process import extractOne, extract
from rapidfuzz.string_metric import levenshtein, normalized_levenshtein, jaro_winkler_similarity
from rapidfuzz.fuzz import ratio
import logging
logging.getLogger().setLevel(logging.ERROR)

# TODO: Correctly register your component with it's type
@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER], is_trainable=False, model_from="SpacyNLP"
)
class RapidFuzzyEntityExtractorForNewKPI(GraphComponent):

    ''' Entity extractor that uses rapidfuzzy library. Example see mitie_entity_extractor.py.'''

    def required_components(cls) -> List[Type]:
        return [Tokenizer, SpacyNLP]

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        """The component's default config (see parent class for full docstring)."""
        return {
            # threshold for filtering 
            "entity_name": "kpi",
            "thres": 0.98,
            "scorer": jaro_winkler_similarity
        }

    def __init__(self, config: Dict[Text, Any]) -> None:
        """Initialize RapidFuzzyEntityExtractorForNewKPI."""
        self._config = config

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:

        return cls(config)

    @staticmethod
    def names_db() -> List[Text]:
        """Database of KPI names"""
        with open('./lookup/New_KPI.txt', 'r', encoding='utf8') as f:
            data = f.read()
            names = data.split('\n')
        return names

    def process(self, messages: List[Message], model: SpacyModel) -> List[Message]:

            thres = self._config.get("thres")
            scorer = self._config.get("scorer")
            names = self.names_db()

            spacy_nlp = model.model
            stopwords = spacy_nlp.Defaults.stop_words

            for message in messages:
                tokens = message.get(TEXT_TOKENS)
                for token in tokens:
                    if token.text.lower() not in stopwords:
                        match, score, idx = extract(token.text, names, scorer=scorer)[0]
                        if score >= thres*100:
                            entities = [
                                        {
                                            "entity": self._config.get("entity_name"),
                                            "value": match,
                                            "start": token.start,
                                            "confidence": score/100,
                                            "end": token.end,
                                            "extractor": "RapidFuzzyEntityExtractorForNewKPI"
                                        }
                                    ]
                            message.set(
                                ENTITIES, message.get(ENTITIES, []) + entities, add_to_output=True
                            )

            return messages