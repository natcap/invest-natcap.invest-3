import os
import math
import logging
import operator
import datetime

from osgeo import ogr
from osgeo import gdal
from invest_natcap import raster_utils

def execute(args):

    '''This is the core module for the management zone model, which was
    extracted from the overlap analysis model. This particular one will take
    in a shapefile conatining a series of AOI's, and a folder containing
    activity layers, and will return a modified shapefile of AOI's, each of
    which will have an attribute stating how many activities take place within
    that polygon.

    Input:
        args['workspace_dir']- The folder location into which we can write an
            Output or Intermediate folder as necessary, and where the final 
            shapefile will be placed.
        args['zone_layer_file']- An open shapefile which contains our
            management zone polygons. It should be noted that this should not
            be edited directly but instead, should have a copy made in order
            to add the attribute field.
        args['overlap_files'] - A dictionary which maps the name of the shapefile
            (excluding the .shp extension) to the open datasource itself. These
            files are each an activity layer that will be counted within the
            totals per management zone.

    Output:
        zone_shapefile- A copy of 'zone_layer_file' with the added attribute 
            "ACTIVITY_COUNT" that will total the number of activities taking
            place in each polygon.
     '''
