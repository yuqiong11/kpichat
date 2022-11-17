PREDEFINED_KPI_MAPPING = {
    ("Ladepunkte", "ladepunkte", "Ladepunkt", "ladepunkt","charging_points", "charging points", "charger_point", "chargingpoint", "Chargingpoints", "Charging_points"): "Charging_points",
    ("locations", "Locations", "Location", "location", "Standorte", "standorte", "Standort", "standort"): "Locations",
    ("charging_stations", "charging_station", "charging stations", "charging station", "charger_station", "chargingstation", "Chargingstations", "Charging_stations","Ladestation", 
    "ladestation", "Ladestationen", "ladestationen"): "Charging_stations",
    ("Cars_per_charging_point", "cars_per_charging_point", "Car_per_charging_point", "car_per_charging_point","Autos pro Ladepunkt", 
    "autos pro ladepunkt", "Autos pro ladepunkt", "autos pro Ladepunkt", "Autos_pro_Ladepunkt", "autos_pro_ladepunkt", 
    "Autos_pro_ladepunkt", "autos_pro_Ladepunkt","Auto pro Ladepunkt", "auto pro ladepunkt", "Auto pro ladepunkt", "auto pro Ladepunkt", "Auto_pro_Ladepunkt",
    "auto_pro_ladepunkt", "auto_pro_Ladepunkt", "Auto_pro_ladepunkt"): "Cars_per_charging_point",
    ("Charging_points_per_1,000_cars", "Charging_point_per_1,000_cars", "Charging_points_per_1,000_car", "Ladepunkte pro 1000 Autos", "ladepunkte pro 1000 autos"
    , "Ladepunkte pro 1000 autos", "ladepunkte pro 1000 Autos", "Ladepunkte_pro_1000_Autos", "ladepunkte_pro_1000_autos", "Ladepunkte_pro_1000_autos",
    "ladepunkte_pro_1000_Autos"): "Charging_points_per_1,000_cars",
    ("Percentage_of_target", "Percentage_target", "Bedarfsdeckung", "bedarfsdeckung", "bedarfserfüllung", "Bedarfserfüllung", "Mindestbedarf", "mindestbedarf", "bedarf", "Bedarf"): "Percentage_of_target"
}


def predefined_kpi_mapping(mapping, input):
    '''
    Given the mapping and input, output the mapped value
    '''

    if type(mapping) is dict:
        for k,v in mapping.items():
            if input in k:
                return v
