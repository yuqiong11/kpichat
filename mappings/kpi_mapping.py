
# class KPIMapping:
#     def __init__(self):
#         pass

#     @staticmethod
#     def mapping_dict():
#         return {
#             "Locations": "no_total_locations",
#             "Charging stations": "no_total_stations",
#             "Charging points": "no_total_chargepoints"
#         }

#     def get_mapping(self, kpi_name):
#         return self.mapping_dict().get(kpi_name)

# mapping = KPIMapping()
# loc_column_name = mapping.get_mapping("Locations")

# print(loc_column_name)


kpi_mapping = {
        "Locations": "no_total_locations",
        "Charging stations": "no_total_stations",
        "Charging points": "no_total_chargepoints"
}


