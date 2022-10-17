from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import overpy
import folium
# import webbrowser

class NearbySearch():
    # queries can be answered
    # how many charging stations are there within 1 km to Spenerstr.28 Berlin? what are they?
    # find the nearest charging stations near Spenerstr.28 Berlin
    
    def __init__(self, timeout, loc):
        self.geolocator = Nominatim(user_agent="my_request")
        self.api = overpy.Overpass()
        self.timeout = timeout
        self.loc = loc
    
    def geocoding(self):
        start_point_geocode = self.geolocator.geocode(self.loc)
        return start_point_geocode.latitude, start_point_geocode.longitude
        

    def radius_search(self,radius=1000):
        start_lat, start_lon = self.geocoding()
        my_query = f"[out:json][timeout:{self.timeout}];nwr['amenity'='charging_station'](around:{radius}, {start_lat}, {start_lon});out center;"
        # return a list of dict of address and distance in sorted order
        # optional: also give some additional information, e.g. provider, type of chagring point, number of charging point
        found_nodes = []
        result = self.api.query(my_query)

        for node in result.nodes:
            node_geocode = (node.lat, node.lon)
            dist = geodesic((start_lat, start_lon), node_geocode).kilometers
            addr = self.geolocator.reverse(node_geocode).address
            found_nodes.append({"addr":addr, "dist":dist, "geocode": node_geocode})

        # order the list 
        found_nodes.sort(key=lambda item: item.get("dist"))

        return found_nodes, len(found_nodes)

    def display_map(self, nodes_list):
        start_lat, start_lon = self.geocoding()
        m = folium.Map(location=[start_lat, start_lon], zoom_start=15)
        for single_node in nodes_list:
            folium.Marker(location=[single_node["geocode"][0], single_node["geocode"][1]], popup=f"{single_node['addr']}").add_to(m)
        m.save('my_map.html')
        # webbrowser.open("my_map.html")


# my_search = NearbySearch(6000, "Spenerstraße 28, 10557 Berlin")
# found_nodes, num_found_nodes = my_search.radius_search(800)
# print(found_nodes)
# my_search.display_map(found_nodes)








####################################################
# from geopy.geocoders import Nominatim
# from geopy.distance import geodesic
# import folium
# import webbrowser
# loc = 'Spenerstraße 28, 10557 Berlin'

# geolocator = Nominatim(user_agent="my_request")
# location = geolocator.geocode(loc)

# print(location.address)
# print((location.latitude, location.longitude))

# import overpy
# api = overpy.Overpass()
# result = api.query("""[out:json][timeout:60];
# (nwr["amenity"="charging_station"](around:500,{{geocodeCoords:Spenerstraße 28, 10557 Berlin}});) -> .results;
# .results out center;""")
# result = api.query("""[out:json][timeout:600];
# nwr["amenity"="charging_station"](around:1000, 52.52170755, 13.353382403050755);
# out center;""")
# distance= []

# for node in result.nodes:
#     # if the node has attribute name, return it, otherwise return n/a
#     # name = node.tags.get("name", "n/a")
#     distance.append(geodesic((location.latitude, location.longitude), (node.lat, node.lon)).kilometers)
#     addr = geolocator.reverse((node.lat, node.lon))
#     print(addr)

# print(distance)


# class NearbySearch():

#     def __init__(self, timeout, loc):
#         self.geolocator = Nominatim(user_agent="my_request")
#         self.api = overpy.Overpass()
#         self.timeout = timeout
#         self.loc = loc
    
#     def geocoding(self):
#         start_point_geocode = self.geolocator.geocode(self.loc)
#         return start_point_geocode.latitude, start_point_geocode.longitude
        

#     def radius_search(self,radius=1000):
#         start_lat, start_lon = self.geocoding()
#         my_query = f"[out:json][timeout:{self.timeout}];nwr['amenity'='charging_station'](around:{radius}, {start_lat}, {start_lon});out center;"
#         # return a list of dict of address and distance in sorted order
#         # optional: also give some additional information, e.g. provider, type of chagring point, number of charging point
#         found_nodes = []
#         result = api.query(my_query)

#         for node in result.nodes:
#             node_geocode = (node.lat, node.lon)
#             dist = geodesic((start_lat, start_lon), node_geocode).kilometers
#             addr = self.geolocator.reverse(node_geocode).address
#             found_nodes.append({"addr":addr, "dist":dist, "geocode": node_geocode})

#         # order the list 
#         found_nodes.sort(key=lambda item: item.get("dist"))

#         return found_nodes

#     def display_map(self, nodes_list):
#         start_lat, start_lon = self.geocoding()
#         m = folium.Map(location=[start_lat, start_lon], zoom_start=15)
#         for single_node in nodes_list:
#             folium.Marker(location=[single_node["geocode"][0], single_node["geocode"][1]], popup=f"{single_node['addr']}").add_to(m)
#         m.save('my_map.html')
#         webbrowser.open("my_map.html")


# my_search = NearbySearch(6000, "Spenerstraße 28, 10557 Berlin")
# found_nodes = my_search.radius_search()
# my_search.display_map(found_nodes)

# import overpass
# api = overpass.API()
# response = api.get('''
# nwr["amenity"="charging_station"](around:500,{{geocodeCoords:Spenerstraße 28, 10557 Berlin}});''', responseformat="json")

# print(response)

# import overpy
# api = overpy.Overpass()
# # result in geojson format
# result = api.query('''[out:json];
# area["name"="Berlin"][admin_level=4];
# (node["amenity"="charging_station"](area);
#  way["amenity"="charging_station"](area);
#  rel["amenity"="charging_station"](area);
# );
# out center;''')
# parse geojson

# import json
# print(type(result))
# data = json.loads(result)
# print(data['feature'][0])


# import overpy
# api = overpy.Overpass()

# min_lat = 50.745
# min_lon = 7.17
# max_lat = 50.75
# max_lon = 7.18

# query = "node(%s, %s, %s, %s);out;" % ( min_lat, min_lon, max_lat, max_lon )
# result = api.query(query)

# print(query)
# print(len(result.nodes))

# api = overpass.API(timeout=500)

# api.get already returns a FeatureCollection, a GeoJSON type
# res = api.get("""
#     area[name="Granollers"][admin_level=8];
#     // query part for: “highway=*”
#     (way["highway"](area);
#       relation["highway"](area);
#     );
# """, verbosity='geom')

# result = api.query('''
# area["name"="Berlin"];
# (nwr["amenity"="charging_station"](area);
# );''')

# print(len(result.nodes))