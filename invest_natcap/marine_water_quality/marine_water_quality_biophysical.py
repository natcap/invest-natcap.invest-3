"""InVEST Marine Water Quality Biophysical module at the "uri" level"""

import sys
import logging
import re
import os
import time
import math
import csv

from osgeo import ogr
from osgeo import gdal
import scipy.sparse.linalg
from scipy.sparse.linalg import spsolve
import numpy as np
from numpy.ma import masked_array
import scipy.linalg
import pylab

from invest_natcap import raster_utils
import marine_water_quality_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('marine_water_quality_biophysical')

def execute(args):
    """Main entry point for the InVEST 3.0 marine water quality 
        biophysical model.

        args - dictionary of string value pairs for input to this model.
        args['workspace'] - output directory.
        args['aoi_poly_uri'] - OGR polygon Datasource indicating region
            of interest to run the model.  Will define the grid.
        args['pixel_size'] - float indicating pixel size in meters
            of output grid.
        args['land_poly_uri'] - OGR polygon DataSource indicating areas where land
            is.
        args['source_points_uri'] - OGR point Datasource indicating point sources
            of pollution.
        args['source_point_data_uri'] - csv file indicating the biophysical
            properties of the point sources.
        args['tide_e_points_uri'] - OGR point Datasource with spatial information 
            about the E parameter
        args['adv_uv_points_uri'] - OGR point Datasource with spatial advection
            u and v vectors."""

    LOGGER.info("Starting MWQ execute")
    aoi_poly = ogr.Open(args['aoi_poly_uri'])
    land_poly = ogr.Open(args['land_poly_uri'])
    land_layer = land_poly.GetLayer()
    source_points = ogr.Open(args['source_points_uri'])
    tide_e_points = ogr.Open(args['tide_e_points_uri'])
    adv_uv_points = ogr.Open(args['adv_uv_points_uri'])

    #Create a grid based on the AOI
    LOGGER.info("Creating grid based on the AOI polygon")
    pixel_size = args['pixel_size']
    #the nodata value will be a min float
    nodata_out = float(np.finfo(np.float32).min)
    raster_out_uri = os.path.join(args['workspace'],'concentration.tif')
    raster_out = raster_utils.create_raster_from_vector_extents(pixel_size, 
        pixel_size, gdal.GDT_Float32, nodata_out, raster_out_uri, aoi_poly)
    
    #create a temporary grid of interpolated points for tide_e and adv_uv
    LOGGER.info("Creating grids for the interpolated tide E and ADV uv points")
    tide_e_raster = raster_utils.new_raster_from_base(raster_out, 'tide_e.tif', 
        'GTiff', nodata_out, gdal.GDT_Float32)
    adv_u_raster = raster_utils.new_raster_from_base(raster_out, 'adv_u.tif',
        'GTiff', nodata_out, gdal.GDT_Float32)
    adv_v_raster = raster_utils.new_raster_from_base(raster_out, 'adv_v.tif',
        'GTiff', nodata_out, gdal.GDT_Float32)
    in_water_raster = raster_utils.new_raster_from_base(raster_out, 'in_water.tif',
        'GTiff', nodata_out, gdal.GDT_Byte)

    #Set up the in_water_array
    LOGGER.info("Calcluating the in_water array")
    in_water_raster_band = in_water_raster.GetRasterBand(1)
    in_water_raster_band.Fill(1)
    gdal.RasterizeLayer(in_water_raster, [1], land_layer, burn_values=[0])
    in_water_array = in_water_raster_band.ReadAsArray()
    in_water_function = np.vectorize(lambda x: x == 1)
    in_water_array = in_water_function(in_water_array)
    
    #Interpolate the ogr datasource points onto a raster the same size as raster_out
    raster_utils.vectorize_points(tide_e_points, 'kh_km2_day', tide_e_raster)
    raster_utils.vectorize_points(adv_uv_points, 'U_m_sec_', adv_u_raster)
    raster_utils.vectorize_points(adv_uv_points, 'V_m_sec_', adv_v_raster)

    #Mask the interpolated points to the land polygon
    LOGGER.info("Masking Tide E and ADV UV to the land polygon")
    for dataset in [tide_e_raster, adv_u_raster, adv_v_raster]:
        band = dataset.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        gdal.RasterizeLayer(dataset, [1], land_layer, burn_values=[nodata])

    #Now we have 3 input rasters for tidal dispersion and uv advection

    #Used for the closure of convert_to_grid_coords below
    LOGGER.info("Converting georeferenced source coordinates to grid coordinates")
    raster_out_gt = raster_out.GetGeoTransform()

    def convert_to_grid_coords(point):
        """Helper to convert source points to numpy grid coordinates

           point - a list of the form [y0,x0]
           
           returns a projected point in the gridspace coordinates of 
               raster_out"""
        
        x_grid = int((point[1]-raster_out_gt[0])/raster_out_gt[1])
        y_grid = int((point[0]-raster_out_gt[3])/raster_out_gt[5])

        return [y_grid, x_grid]


    #Set up the source point data structure

    #Load the point source data CSV file.
    source_point_values = {}

    LOGGER.info("Load the point sources")
    source_layer = source_points.GetLayer()
    aoi_layer = aoi_poly.GetLayer()
    aoi_polygon = aoi_layer.GetFeature(0)
    aoi_geometry = aoi_polygon.GetGeometryRef()
    source_point_list = []
    for point_feature in source_layer:
        point_geometry = point_feature.GetGeometryRef()
        if aoi_geometry.Contains(point_geometry):
            point = point_geometry.GetPoint()
            point_id = point_feature.GetField('id')
            LOGGER.debug("point and id %s %s" % (point,point_id))
            #Appending point geometry with y first so it can be converted
            #to the numpy (row,col) 2D notation easily.
            source_point_values[point_id] = {
                'point': convert_to_grid_coords([point[1],point[0]])
                }

    csv_file = open(args['source_point_data_uri'])
    reader = csv.DictReader(csv_file)
    for row in reader:
        point_id = int(row['ID'])
        if point_id not in source_point_values:
            LOGGER.warn("%s is an id defined in the data table which is not found in the shapefile. Ignoring that point." % (point_id))
            continue

        #This merges the current dictionary with a new one that includes KPS and WPS
        source_point_values[point_id] = \
            dict(source_point_values[point_id].items() + {
                'KPS': float(row['KPS']),
                'WPS': float(row['WPS'])}.items())

    LOGGER.info("Checking to see if all the points have KPS and WPS values")
    points_to_ignore = []
    for point_id in source_point_values:
        if 'KPS' not in source_point_values[point_id]:
            LOGGER.warn("point %s has no source parameters from the CSV.  Ignoring that point." %
                        point_id)
            #Can't delete out of the dictionary that we're iterating over
            points_to_ignore.append(point_id)
    #Deleting the points we don't have data for
    for point in points_to_ignore:
        del source_point_values[point]

    #Convert the georeferenced source coordinates to grid coordinates
    LOGGER.info("Solving advection/diffusion equation")

    tide_e_band = tide_e_raster.GetRasterBand(1)
    adv_u_band = adv_u_raster.GetRasterBand(1)
    adv_v_band = adv_v_raster.GetRasterBand(1)

    tide_e_array = tide_e_band.ReadAsArray()
    #convert E from km^2/day to m^2/sec
    LOGGER.info("Convert tide E form km^2/day to m^2/sec")
    tide_e_array[tide_e_array != nodata_out] *= 1000.0 ** 2 / 86400.0


    adv_u_array = adv_u_band.ReadAsArray()
    adv_v_array = adv_v_band.ReadAsArray()

    #If the cells are square then it doesn't matter if we look at x or y
    #but if different, we need just one value, so take the average.  Not the
    #best, but better than nothing.
    cell_size = raster_out_gt[1]
    if abs(raster_out_gt[1]) != abs(raster_out_gt[5]):
        LOGGER.warn("Warning, cells aren't square, so the results of the solver will be incorrect")

    concentration_array = \
        marine_water_quality_core.diffusion_advection_solver(source_point_values,
        in_water_array, tide_e_array, adv_u_array, adv_v_array, nodata_out, 
        cell_size)

    raster_out_band = raster_out.GetRasterBand(1)
    raster_out_band.WriteArray(concentration_array, 0, 0)

    LOGGER.info("Done with MWQ execute")
