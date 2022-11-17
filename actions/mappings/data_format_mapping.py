# this script helps with mapping data structures from python to other structures in mongodb
from time import time
from db import Querymethods

class MapDataFormat():
    '''
    The class for mapping
    '''
    make_query = Querymethods()

    def __init__(self):
        self.params = []
        self.entries = []

    def split_dict(self, my_dict, new_knowledge_list, **additionals):
        # To check for each k,v pair if it's new param or new entry
        # split into 2 lists

        # if provided_entries or provided_params:

        #     if provided_params:
        #         self.params = provided_params

        #     if provided_entries:
        #         self.entries = provided_entries

        for k,v in my_dict.items():
            if k in new_knowledge_list:
                entry = (v, additionals["place"], additionals["time"])
                if self.make_query.find_value("statistics", "name", k, "entries"):
                    self.entries.append({"name": k, "entries": entry})
                else:
                    self.params.append({"name": k, "entries": [entry]})

    def add_new_params(self, provided_params):
        # add new params with its entries
        if provided_params:
            self.make_query.insert_docu("statistics", provided_params)
        else:
            if self.params:
                self.make_query.insert_docu("statistics", self.params)

    def add_new_entries(self, provided_entries):
        # add new entries into existing params
        if provided_entries:
            for entry in provided_entries:
                self.make_query.update_value("statistics", "name", "entries", entry["name"], entry["entries"])
        else:
            if self.entries:
                for entry in self.entries:
                    self.make_query.update_value("statistics", "name", "entries", entry["name"], entry["entries"])
