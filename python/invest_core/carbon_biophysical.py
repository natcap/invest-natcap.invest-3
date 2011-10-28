"""InVEST Carbon Modle file handler module"""

import sys, os
import simplejson as json
import carbon_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['calculate_sequestration'] - a boolean, True if sequestration
            is to be calculated.  Infers that args['lulc_fut_uri'] should be 
            set.
        args['calculate_hwp'] - a boolean, True if harvested wood product
            calcuation is to be done.  Also implies a sequestration 
            calculation.  Thus args['lulc_fut_uri'], args['hwp_cur_shape_uri'],
            args['hwp_fut_shape_uri'], args['lulc_cur_year'], and 
            args['lulc_fut_year'] should be set.
        args['calc_uncertainty'] - a Boolean.  True if we wish to calculate 
            uncertainty in the carbon model.  Implies that carbon pools should
            have value ranges
        args['uncertainty_percentile'] - the percentile cutoff desired for 
            uncertainty calculations (required if args['calc_uncertainty'] is 
            True) 
        args['lulc_cur_uri'] - is a uri to a GDAL raster dataset (required)
        args['lulc_fut_uri'] - is a uri to a GDAL raster dataset (required
         if calculating sequestration or HWP)
        args['lulc_cur_year'] - An integer representing the year of lulc_cur 
            used in HWP calculation (required if args['calculate_hwp'] is True)
        args['lulc_fut_year'] - An integer representing the year of  lulc_fut
            used in HWP calculation (required if args['calculate_hwp'] is True)
        args['carbon_pools_uri'] - is a uri to a DBF dataset mapping carbon 
            storage density to the lulc classifications specified in the
            lulc rasters.  If args['calc_uncertainty'] is True the columns
            should have additional information about min, avg, and max carbon
            pool measurements. 
        args['hwp_cur_shape_uri'] - Current shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True) 
        args['hwp_fut_shape_uri'] - Future shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True)
        
        returns nothing."""

    #This ensures we are not in Arc's python directory so that when
    #we import gdal stuff we don't get the wrong GDAL version.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    gdal.AllRegister()

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the biophysical core model
    biophysicalArgs = {}

    #Uncertainty percentage is required if calculating uncertainty
    if args['calc_uncertainty']:
        biophysicalArgs['uncertainty_percentile'] = \
            args['uncertainty_percentile']

    #lulc_cur is always required
    biophysicalArgs['lulc_cur'] = gdal.Open(args['lulc_cur_uri'],
                                            gdal.GA_ReadOnly)

    #a future lulc is only required if sequestering or hwp calculating
    if args['calculate_sequestration'] or args['calculate_hwp']:
        biophysicalArgs['lulc_fut'] = gdal.Open(args['lulc_fut_uri'],
                                            gdal.GA_ReadOnly)

    #Years and harvest shapes are required if doing HWP calculation
    if args['calculate_hwp']:
        for x in ['lulc_cur_year', 'lulc_fut_year']:
            biophysicalArgs[x] = args[x]
        fsencoding = sys.getfilesystemencoding()
        for x in ['hwp_cur_shape', 'hwp_fut_shape']:
            biophysicalArgs[x] = ogr.Open(args[x + '_uri'].encode(fsencoding))

    #Always need carbon pools, if uncertainty calculation they also need
    #to have range columns in them, but no need to check at this level.
    biophysicalArgs['carbon_pools'] = dbf.Dbf(args['carbon_pools_uri'])

    #At this point all inputs are loaded into biophysicalArgs.  The 
    #biophysical model also needs temporary and output files to do its
    #calculation.  These are calculated next.

    #These lines sets up the output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output'
    intermediateDirectoryPrefix = args['workspace_dir'] + os.sep + \
        'Intermediate'

    #This defines a dictionary that links output/temporary GDAL/OAL objects
    #to their locations on disk.  Helpful for creating the objects in the next 
    #step
    outputURIs = {}
    outputURIs['tot_C_cur'] = outputDirectoryPrefix + 'tot_C_cur.tif'
    if args['calculate_sequestration'] or args['calculate_hwp']:
        outputURIs['tot_C_fut'] = outputDirectoryPrefix + 'tot_C_fut.tif'
        outputURIs['sequest'] = outputDirectoryPrefix + 'sequest.tif'

    #If we calculate uncertainty, we need to generate the colorized map that
    #Highlights the percentile ranges
    if args['calc_uncertainty']:
        outputURIs['uncertainty_percentile_map'] = outputDirectoryPrefix + \
            'uncertainty_colormap.tif'

    #If we're doing a HWP calculation, we need temporary rasters to hold the
    #HWP pools
    if args['calculate_hwp']:
        outputURIs['bio_hwp_cur'] = intermediateDirectoryPrefix + \
            'bio_hwp_cur.tif'
        outputURIs['bio_hwp_fut'] = intermediateDirectoryPrefix + \
            'bio_hwp_fut.tif'
        outputURIs['vol_hwp_cur'] = intermediateDirectoryPrefix + \
            'vol_hwp_cur.tif'
        outputURIs['vol_hwp_fut'] = intermediateDirectoryPrefix + \
            'vol_hwp_fut.tif'

    #Create the output and intermediate rasters to be the same size/format as
    #the base LULC
    for datasetName, datasetPath in outputURIs.iteritems():
        biophysicalArgs[datasetName] = \
            newRasterFromBase(biophysicalArgs['lulc_cur'], datasetPath,
                              'GTiff', -5.0, gdal.GDT_Float32)

    #run the biophysical part of the carbon model.
    carbon.biophysical(biophysicalArgs)

    #close the pools DBF file (is this required?)
    biophysicalArgs['carbon_pools'].close()

    #close all newly created raster datasets (is this required?)
    for dataset in biophysicalArgs:
        biophysicalArgs[dataset] = None



def newRasterFromBase(base, outputURI, format, nodata, datatype):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
        base - a the GDAL raster dataset to base output size, and transforms on
        outputURI - a string URI to the new output raster dataset.
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
                
        returns a new GDAL raster dataset."""

    cols = base.RasterXSize
    rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()

    driver = gdal.GetDriverByName(format)
    newRaster = driver.Create(outputURI, cols, rows, 1, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    newRaster.GetRasterBand(1).SetNoDataValue(nodata)

    return newRaster

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
