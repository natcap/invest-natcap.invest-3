"""InVEST Sediment biophysical module at the "uri" level"""

import sys
import os
import csv
import logging

import json
from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import routing_cython_core
from invest_natcap.sediment import sediment_core


logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sediment_biophysical')


def execute(args):
    """This function invokes the biophysical part of the sediment model given
        URI inputs of files. It will do filehandling and open/create
        appropriate objects to pass to the core sediment biophysical
        processing function.  It may write log, warning, or error messages to
        stdout.

        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['dem_uri'] - a uri to a digital elevation raster file (required)
        args['erosivity_uri'] - a uri to an input raster describing the
            rainfall eroisivity index (required)
        args['erodibility_uri'] - a uri to an input raster describing soil
            erodibility (required)
        args['landuse_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical
            properties of the landscape.  (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['subwatersheds_uri'] - a uri to an input shapefile of the
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['reservoir_locations_uri'] - a uri to an input shape file with
            points indicating reservoir locations with IDs. (optional)
        args['reservoir_properties_uri'] - a uri to an input CSV table
            describing properties of input reservoirs provided in the
            reservoirs_uri shapefile (optional)
        args['biophysical_table_uri'] - a uri to an input CSV file with
            biophysical information about each of the land use classes.
        args['threshold_flow_accumulation'] - an integer describing the number
            of upstream cells that must flow int a cell before it's considered
            part of a stream.  required if 'v_stream_uri' is not provided.
        args['slope_threshold'] - A percentage slope threshold as described in
            the user's guide.

        returns nothing."""

    csv_dict_reader = csv.DictReader(open(args['biophysical_table_uri']))
    biophysical_table = {}
    for row in csv_dict_reader:
        biophysical_table[int(row['lucode'])] = row

    intermediate_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Sets up the intermediate and output directory structure for the workspace
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.debug('creating directory %s', directory)
            os.makedirs(directory)


    dem_dataset = gdal.Open(args['dem_uri'])
    n_rows = dem_dataset.RasterYSize
    n_cols = dem_dataset.RasterXSize
    
    #Calculate slope
    LOGGER.info("Calculating slope")
    slope_uri = os.path.join(intermediate_dir, 'slope.tif')
    slope_dataset = raster_utils.calculate_slope(dem_dataset, slope_uri)

    #Calcualte flow accumulation
    LOGGER.info("calculating flow accumulation")
    flow_accumulation_uri = os.path.join(intermediate_dir, 'flow_accumulation.tif')
    routing_utils.flow_accumulation(args['dem_uri'], flow_accumulation_uri)

    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    v_stream_uri = os.path.join(intermediate_dir, 'v_stream.tif')

    stream_dataset = routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)


    flow_direction_uri = os.path.join(intermediate_dir, 'flow_direction.tif')
    ls_uri = os.path.join(intermediate_dir, 'ls.tif')
    routing_cython_core.flow_direction_inf(args['dem_uri'], flow_direction_uri)

    #Calculate LS term
    ls_nodata = -1.0
    sediment_core.calculate_ls_factor(flow_accumulation_uri, slope_uri,
                                      flow_direction_uri, ls_uri, ls_nodata)

    lulc_dataset = gdal.Open(args['landuse_uri'])
    retention_uri = os.path.join(intermediate_dir, 'retention.tif')

    LOGGER.info('building alpha raster from lulc')
    lulc_to_alpha_dict = dict([(lulc_code, float(table['alpha'])) for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_retention_dict %s' % lulc_to_alpha_dict)
    raster_utils.reclassify_dataset(
        lulc_dataset, lulc_to_alpha_dict, retention_uri, gdal.GDT_Float32,
        -1.0, exception_flag='values_required')

    
    LOGGER.info('building cp raster from lulc')
    lulc_to_cp_dict = dict([(lulc_code, float(table['usle_c']) * float(table['usle_p']))  for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_cp_dict %s' % lulc_to_cp_dict)

    LOGGER.info('building (1-c)(1-p) raster from lulc')


    return



















    LOGGER.info('Loading data sources')

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the biophysical core model
    biophysical_args = {}

    #load shapefiles
    for shapefile_name in ['watersheds',
                           'subwatersheds',
                           'reservoir_locations']:
        fsencoding = sys.getfilesystemencoding()
        uri_name = shapefile_name + '_uri'
        if uri_name in args:
            biophysical_args[shapefile_name] = \
                ogr.Open(args[uri_name].encode(fsencoding))
            LOGGER.debug('load %s as: %s' % (args[uri_name],
                biophysical_args[shapefile_name]))

    #load and clip rasters
    for raster_name in ['dem', 'erosivity', 'erodibility', 'landuse']:
        original_dataset = gdal.Open(args[raster_name + '_uri'],
                                     gdal.GA_ReadOnly)
        clipped_uri = os.path.join(intermediate_dir, raster_name + "_clip.tif")
        biophysical_args[raster_name] = \
            raster_utils.clip_dataset(original_dataset,
            biophysical_args['watersheds'], clipped_uri)
        LOGGER.debug('load %s as: %s' % (args[raster_name + '_uri'],
                                         biophysical_args[raster_name]))

    #check that they have the same projection
    for raster_name in ['dem', 'erosivity', 'erodibility', 'landuse']:
        LOGGER.debug(biophysical_args[raster_name].GetProjection())

    #build up each table into a python dictionary
    data_tables = [('reservoir_properties', 'id'), 
                   ('biophysical_table', 'lucode')]
    for value, column_name in data_tables:
        try:
            csv_dict_reader = csv.DictReader(open(args[value + '_uri']))
            id_table = {}
            for row in csv_dict_reader:
                id_table[row[column_name]] = row
            biophysical_args[value] = id_table
        except (IOError, KeyError), error:
            #Get here if file value is not found
            LOGGER.warning(error)

    #primatives
    for value in ['threshold_flow_accumulation', 'slope_threshold']:
        biophysical_args[value] = args[value]
        LOGGER.debug('%s=%s' % (value, biophysical_args[value]))

    #build output rasters
    #This defines a dictionary that links output/temporary GDAL/OAL objects
    #to their locations on disk.  Helpful for creating the objects in the
    #next step
    output_uris = {}
    intermediate_rasters = ['flow_direction', 'flow_accumulation', 'slope',
                            'ls_factor', 'v_stream']
    for base_name in intermediate_rasters:
        output_uris[base_name] = os.path.join(intermediate_dir, base_name + '.tif')

    #Create the output and intermediate rasters to be the same size/format as
    #the base LULC
    for raster_name, raster_path in output_uris.iteritems():
        LOGGER.debug('creating output raster %s', raster_path)
        biophysical_args[raster_name] = \
            raster_utils.new_raster_from_base(biophysical_args['dem'],
                              raster_path, 'GTiff', -5.0, gdal.GDT_Float32)

    #We won't know the size of the output rasters until we vectorize the stack
    #of input rasters.  So we just pass a uri to its final location to the
    #biophysical part.
    output_uris = ['sret_dr', 'sexp_dr', 'slope', 'v_stream', 'ls', 'usle']
    for raster_id in output_uris:
        biophysical_args[raster_id + '_uri'] = \
            os.path.join(output_dir,raster_id + '.tif')

    biophysical_args['intermediate_uri'] = intermediate_dir
    biophysical_args['output_uri'] = output_dir

    LOGGER.info('starting biophysical model')
    sediment_core.biophysical(biophysical_args)
    LOGGER.info('finished biophysical model')

    LOGGER.info('generating report')

    #Load the relevant output datasets so we can output them in the report
    pixel_export_dataset = \
        gdal.Open(os.path.join(output_dir, 'pixel_export.tif'))
    pixel_retained_dataset = \
        gdal.Open(os.path.join(output_dir, 'pixel_retained.tif'))

    #Output table for watersheds
    output_table_uri = os.path.join(output_dir, 'sediment_watershed.csv')
    sediment_core.generate_report(pixel_export_dataset, pixel_retained_dataset,
        biophysical_args['watersheds'], output_table_uri)

    #Output table for subwatersheds
    output_table_uri = os.path.join(output_dir, 'sediment_subwatershed.csv')
    sediment_core.generate_report(pixel_export_dataset, pixel_retained_dataset,
        biophysical_args['subwatersheds'], output_table_uri)


#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    MODULE_NAME, JSON_ARGS = sys.argv
    MAIN_ARGS = json.loads(JSON_ARGS)
    execute(MAIN_ARGS)
