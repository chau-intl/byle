# -*- coding: utf-8 -*-
from osgeo import ogr
import os
import pyperclip

class City(object):

    region = None

    def __init__(self, name, id, population, geometry):
        self.name = name
        self.id = id
        self.population = population
        self.geometry = geometry.Clone()


class DataLoader(object):

    def __init__(self):
        pass


    def get_country_data(self, folder):

        geometry = ogr.Geometry(ogr.wkbMultiPolygon)

        driver = ogr.GetDriverByName('GML')
        in_ds = driver.Open(os.path.join(folder, 'dagi_10m_nohist_l1.kommuneinddeling.gml'))
        in_layer = in_ds.GetLayerByIndex(0)

        current_feature = in_layer.GetNextFeature()

        while current_feature is not None:
            # Handle multi polygons.
            for i in range(current_feature.GetGeometryRef().GetGeometryCount()):
                geometry.AddGeometry(current_feature.GetGeometryRef().GetGeometryRef(i).Buffer(1).Clone())            

            current_feature = in_layer.GetNextFeature()

        return geometry.UnionCascaded()


    def get_city_data(self, folder):

        result = {}

        driver = ogr.GetDriverByName('GML')
        in_ds = driver.Open(os.path.join(folder, 'bebyggelse.gml'))
        in_layer = in_ds.GetLayerByIndex(0)

        count = 0
        in_layer.SetAttributeFilter("bebyggelsestype = 'by' AND indbyggertal > 5000")
        total = in_layer.GetFeatureCount()    
        current_feature = in_layer.GetNextFeature()

        while current_feature is not None:
            count += 1

            item_id = current_feature.GetFieldAsInteger('bebyggelseskode')
            name = current_feature.GetFieldAsString('navn_1_skrivemaade')
            population = current_feature.GetFieldAsInteger('indbyggertal')

            result[item_id] = City(name, item_id, population, current_feature.GetGeometryRef())
            current_feature = in_layer.GetNextFeature()

            #if count > 15:
            #    break

        return result


    def add_region_attributes(self, cities, folder):
        driver = ogr.GetDriverByName('GML')
        in_ds = driver.Open(os.path.join(folder, 'dagi_10m_nohist_l1.landsdel.gml'))
        in_layer = in_ds.GetLayerByIndex(0)

        regions = []
        count = 0
        total = in_layer.GetFeatureCount()    
        current_feature = in_layer.GetNextFeature()

        while current_feature is not None:
            count += 1

            regions.append((current_feature.GetFieldAsString('navn'), current_feature.GetGeometryRef().Clone()))
            current_feature = in_layer.GetNextFeature()

            #if count > 15:
            #    break

        for city_name, city in cities.items():
            # Use the centroid to determine which region a city is located within.

            for region in regions:
                if region[1].Contains(city.geometry.Centroid()):
                    city.region = region[0]
                    break

        a = 1