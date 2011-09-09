"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import carbon_scenario_uncertainty
from osgeo import gdal
from osgeo.gdalconst import *
from dbfpy import dbf

def execute(args):
    """This function invokes the carbon uncertainty model given uri
    inputs of files.
    
    args - a dictionary object of arguments"""

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    driver = gdal.GetDriverByName("GTIFF")
    lulc_cur = gdal.Open(args['lulc_cur_uri'], GA_ReadOnly)
    lulc_fut = gdal.Open(args['lulc_fut_uri'], GA_ReadOnly)
    output_seq = driver.Create(args['output_dir'] + 'uncertainty_sequestration.tif',
                           lulc_cur.GetRasterBand(1).XSize,
                           lulc_cur.GetRasterBand(1).YSize, 1, gdal.GDT_Float32)
    output_seq.GetRasterBand(1).SetNoDataValue(0)
    output_seq.SetGeoTransform(lulc_cur.GetGeoTransform())
    output_map = driver.Create(args['output_dir'] + 'uncertainty_colormap.tif',
                           lulc_cur.GetRasterBand(1).XSize,
                           lulc_cur.GetRasterBand(1).YSize, 1, gdal.GDT_Byte)
    output_map.GetRasterBand(1).SetNoDataValue(255)
    output_map.SetGeoTransform(lulc_cur.GetGeoTransform())

    args = { 'lulc_cur': lulc_cur,
            'lulc_fut': lulc_fut,
            'carbon_pools': dbf.Dbf(args['carbon_pools_uri']),
            'output_seq': output_seq,
            'output_map': output_map,
            'percentile': args['percentile']}

    carbon_scenario_uncertainty.execute(args)

    #This is how GDAL closes its datasets in python
    output = None

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    print sys.argv
    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
