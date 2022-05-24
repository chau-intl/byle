# -*- coding: utf-8 -*-
from osgeo import gdal, ogr
from gdal_error_handler import GdalErrorHandler

import datetime
import os
import pyperclip

from list_creator import ListCreator
from image_creator import ImageCreator
from relations_creator import RelationsCreator
from data_loader import DataLoader


if __name__ == "__main__":
    err = GdalErrorHandler()
    gdal.PushErrorHandler(err.handler)
    gdal.UseExceptions()  # Exceptions will get raised on anything >= gdal.CE_Failure

    project_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    input_data_folder = os.path.join(project_folder, 'input_data')
    public_folder = os.path.join(project_folder, 'public')
    data_folder = os.path.join(public_folder, 'data')
    image_folder = os.path.join(public_folder, 'images')
    max_image_size = 512

    # More colorblind friendly colours.
    polygon_color = [77,172,38,255]
    highlight_color = [208,28,139,255]

    loader = DataLoader()
    cities = loader.get_city_data(input_data_folder)
    loader.add_region_attributes(cities, input_data_folder)

    country_polygon = loader.get_country_data(input_data_folder)
       
    relations_creator = RelationsCreator()
    print('Calculating relations...')
    relations = relations_creator.calculate(cities)

    list_creator = ListCreator()
    print('Creating data lists...')
    # Create JSON data.
    list_creator.create_relations_list_json(relations, data_folder)
    list_creator.create_city_list_json(cities, data_folder)
    list_creator.create_date_list_json(cities, datetime.datetime.now() + datetime.timedelta(days=0), data_folder)

    # Create images.
    image_creator = ImageCreator(country_polygon)
    image_creator.run(cities, max_image_size, polygon_color, highlight_color, image_folder)

    gdal.PopErrorHandler()