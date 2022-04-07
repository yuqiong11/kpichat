from turtle import update
from time_mapping import convert_time
from kpi_mapping import KPI_MAPPING
from sql_mapping import load_query_clusters, add_new_data
import sys
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/own_models'
sys.path.insert(0, path)
from sentence_transformer import output_template, DEFAULT_PARAMS
path = 'e:/User/yuqiong.weng/Chatbot/kpibot/utils'
sys.path.insert(0, path)
from constants import STATE_LIST, QUERY_CLUSTERS_PATH

DEFAULT_PARAMS['load_centroids'] = True

class QueryTranslation:

    def __init__(self, kpi, place, DATE, entities_indices, user_input, intent):
        self.kpi = kpi
        self.place = place
        self.DATE = DATE
        self.entities_indices = entities_indices
        self.user_input = user_input
        self.intent = intent
        self.cluster_name = None

    def kpi_mapping(self):
        return KPI_MAPPING.get(f"{self.kpi}")

    def time_mapping(self):
        return convert_time(self.DATE)

    def mask(self):
        kpi_start, kpi_end = self.entities_indices.get('kpi_idx')['start'], self.entities_indices.get('kpi_idx')['end']
        place_start, place_end = self.entities_indices.get('place_idx')['start'], self.entities_indices.get('place_idx')['end']
        DATE_start, DATE_end = self.entities_indices.get('DATE_idx')['start'], self.entities_indices.get('DATE_idx')['end']
        kpi_raw = self.user_input[kpi_start:kpi_end]
        place_raw = self.user_input[place_start:place_end]
        DATE_raw = self.user_input[DATE_start:DATE_end]

        masked_query = self.user_input.replace(kpi_raw, "[kpi]")
        masked_query = masked_query.replace(DATE_raw, "[mapped_time]")

        if self.place not in ('Germany','state','county','federal state','states','counties','federal states'):
            if self.place in STATE_LIST:
                masked_query = masked_query.replace(place_raw, "[place_state]")
            else:
                masked_query = masked_query.replace(place_raw, "[place_county]")

        print(masked_query)

        return masked_query

    def sql_mapping(self):
        masked_query = self.mask()
        template, cluster_name = output_template(masked_query, self.intent, **DEFAULT_PARAMS)
        self.cluster_name = cluster_name
        return template

    def vaild_sql(self):
        mapped_kpi = self.kpi_mapping()
        mapped_time = self.time_mapping()

        output_sql = self.sql_mapping()
        if '{kpi}' in output_sql:
            output_sql = output_sql.replace('{kpi}', mapped_kpi)
        if '{mapped_time}' in output_sql:
            output_sql = output_sql.replace('{mapped_time}', mapped_time)        
        if '{place}' in output_sql:
            output_sql = output_sql.replace('{place}', self.place)

        print(output_sql)
  
        return output_sql

    def update_clusters(self, update_signal):
        if update_signal:
            masked_q = self.mask()
            cluster_name = self.cluster_name
            add_new_data(QUERY_CLUSTERS_PATH, masked_q, self.intent, cluster_name)
        else:
            pass





    