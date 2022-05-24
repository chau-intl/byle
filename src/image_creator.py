# -*- coding: utf-8 -*-
from osgeo import gdal, ogr

import math
import numpy as np
import os
import pyperclip


class ImageCreator(object):

    def __init__(self, country_polygon):
        self.country_polygon = country_polygon.Clone()


    def create_raster_ds(self, geometry, max_size):

        cols = max_size
        rows = max_size
        bbox = geometry.GetEnvelope()

        width = bbox[1] - bbox[0]
        height = bbox[3] - bbox[2]

        if width > height:
            rows = math.ceil(max_size * height / width)
        else:
            cols = math.ceil(max_size * width / height)
        geotransform = [bbox[0], width / cols, 0, bbox[2], 0, height / rows]

        raster_ds = gdal.GetDriverByName('MEM').Create('', cols, rows, 4, gdal.GDT_Byte)
        raster_ds.SetGeoTransform(geotransform)

        return raster_ds


    def create_vector_layer(self, geometry):
        vector_ds = ogr.GetDriverByName('Memory').CreateDataSource('wrk')
        mem_layer = vector_ds.CreateLayer('poly')

        f = ogr.Feature(mem_layer.GetLayerDefn())
        f.SetGeometry(geometry)
        mem_layer.CreateFeature(f)

        return vector_ds, mem_layer


    def flip_image(self, raster_ds):
        # Flip the image up-down.
        data = raster_ds.ReadAsArray()
        for i in range(data.shape[0]):
            data[i] = np.flipud(data[i])

        raster_ds.WriteArray(data)

        return raster_ds


    def run(self, features, max_size, polygon_color, highlight_color, folder):

        print('Creating {} images...'.format(len(features) * 2))        

        country_raster_ds = self.create_raster_ds(self.country_polygon, max_size)

        vector_ds, mem_layer = self.create_vector_layer(self.country_polygon)

        # Rasterize the country only.
        err = gdal.RasterizeLayer(country_raster_ds, [1,2,3,4], mem_layer, burn_values=polygon_color, options=['ALL_TOUCHED=TRUE'])

        # Save the rasterization for later reuse.
        country_data = country_raster_ds.ReadAsArray()

        for id, feature in features.items():
            
            out_image_filename = os.path.join(folder, str(id) + '.png')
            out_result_filename = os.path.join(folder, str(id) + '_result.png')

            raster_ds = self.create_raster_ds(feature.geometry, max_size)

            vector_ds, mem_layer = self.create_vector_layer(feature.geometry)

            # Rasterize the municipality.
            err = gdal.RasterizeLayer(raster_ds, [1,2,3,4], mem_layer, burn_values=highlight_color, options=['ALL_TOUCHED=TRUE'])

            # Flip image to fit non geographical view.
            raster_ds = self.flip_image(raster_ds)

            # Save the municipality image.
            out_ds = gdal.GetDriverByName('PNG').CreateCopy(out_image_filename, raster_ds, strict=0)
            out_ds = None

            # Create result image.

            # Reuse country data.
            country_raster_ds.WriteArray(country_data)

            # Rasterize the current municipality into the country.
            err = gdal.RasterizeLayer(country_raster_ds, [1,2,3,4], mem_layer, burn_values=highlight_color, options=['ALL_TOUCHED=TRUE'])

            # Flip image to fit non geographical view.
            country_raster_ds = self.flip_image(country_raster_ds)

            # Save the result image.
            out_ds = gdal.GetDriverByName('PNG').CreateCopy(out_result_filename, country_raster_ds, strict=0)
            out_ds = None

            # Remove the xml files created.
            os.remove(out_image_filename + '.aux.xml')
            os.remove(out_result_filename + '.aux.xml')