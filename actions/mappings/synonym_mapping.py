PREDEFINED_KPI_MAPPING = {
    ("charging_points", "charging points", "charger_point", "chargingpoint", "chargingpoints", "charging_points"): "Charging_points",
    ("locations", "Locations", "Location", "location"): "Locations",
    ("charging_stations", "charging_station", "charging stations", "charging station", "charger_station", "chargingstation", "chargingstations", "charging_stations"): "Charging_stations",
    ("cars_per_charging_point", "cars_per_charging_point", "car_per_charging_point", "car_per_charging_point"): "Cars_per_charging_point",
    ("charging_points_per_1,000_cars", "charging_point_per_1,000_cars", "charging_points_per_1,000_car"): "Charging_points_per_1,000_cars",
    ("percentage_of_target", "percentage_target", "percentage_of_targets", "percentage_of_targets", "percentage", "percentage_target", "target"): "Percentage_of_target"
}


def predefined_kpi_mapping(mapping, input):
    '''
    Given the mapping and input, output the mapped value
    '''

    if type(mapping) is dict:
        for k,v in mapping.items():
            if input.lower() in k:
                return v
