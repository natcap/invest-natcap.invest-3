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

    out_pixel_size = raster_utils.pixel_size(gdal.Open(args['landuse_uri']))

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
    _, dem_nodata = raster_utils.extract_band_and_nodata(dem_dataset)
    
    clipped_dem_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [args['dem_uri']], lambda x: float(x), clipped_dem_uri,
        gdal.GDT_Float32, dem_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])

    #Calculate slope
    LOGGER.info("Calculating slope")
    slope_uri = os.path.join(intermediate_dir, 'slope.tif')
    raster_utils.calculate_slope(clipped_dem_uri, slope_uri)

    #Calcualte flow accumulation
    LOGGER.info("calculating flow accumulation")
    flow_accumulation_uri = os.path.join(intermediate_dir, 'flow_accumulation.tif')
    routing_utils.flow_accumulation(clipped_dem_uri, flow_accumulation_uri)

    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    v_stream_uri = os.path.join(intermediate_dir, 'v_stream.tif')

    routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)

    flow_direction_uri = os.path.join(intermediate_dir, 'flow_direction.tif')
    ls_uri = os.path.join(intermediate_dir, 'ls.tif')
    routing_cython_core.calculate_flow_direction(clipped_dem_uri, flow_direction_uri)

    #Calculate LS term
    LOGGER.info('calcualte ls term')
    ls_nodata = -1.0
    sediment_core.calculate_ls_factor(flow_accumulation_uri, slope_uri,
                                      flow_direction_uri, ls_uri, ls_nodata)

    #Clip the LULC
    lulc_dataset = gdal.Open(args['landuse_uri'])
    _, lulc_nodata = raster_utils.extract_band_and_nodata(lulc_dataset)
    lulc_clipped_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [args['landuse_uri']], lambda x: int(x), lulc_clipped_uri,
        gdal.GDT_Int32, lulc_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])
    lulc_clipped_dataset = gdal.Open(lulc_clipped_uri)


    export_rate_uri = os.path.join(intermediate_dir, 'export_rate.tif')

    LOGGER.info('building export fraction raster from lulc')
    #dividing sediment retention by 100 since it's in the csv as a percent then subtracting 1.0 to make it export
    lulc_to_export_dict = \
        dict([(lulc_code, 1.0 - float(table['sedret_eff'])/100.0) \
                  for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_export_dict %s' % lulc_to_export_dict)
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_export_dict, export_rate_uri, gdal.GDT_Float32,
        -1.0, exception_flag='values_required')
    
    LOGGER.info('building cp raster from lulc')
    lulc_to_cp_dict = dict([(lulc_code, float(table['usle_c']) * float(table['usle_p']))  for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_cp_dict %s' % lulc_to_cp_dict)
    cp_uri = os.path.join(intermediate_dir, 'cp.tif')
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_cp_dict, cp_uri, gdal.GDT_Float32,
        -1.0, exception_flag='values_required')

    LOGGER.info('building (1-c)(1-p) raster from lulc')
    lulc_to_inv_cp_dict = dict([(lulc_code, (1.0-float(table['usle_c'])) * (1.0-float(table['usle_p'])))  for (lulc_code, table) in biophysical_table.items()])

    LOGGER.debug('lulc_to_inv_cp_dict %s' % lulc_to_inv_cp_dict)
    inv_cp_uri = os.path.join(intermediate_dir, 'cp_inv.tif')
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_inv_cp_dict, inv_cp_uri, gdal.GDT_Float32,
        -1.0, exception_flag='values_required')

    LOGGER.info('calculating usle')
    usle_uri = os.path.join(output_dir, 'usle.tif')
    sediment_core.calculate_potential_soil_loss(
        ls_uri, args['erosivity_uri'], args['erodibility_uri'], cp_uri,
        v_stream_uri, usle_uri)

    effective_export_to_stream_uri = os.path.join(intermediate_dir, 'effective_export_to_stream.tif')

    outflow_weights_uri = os.path.join(intermediate_dir, 'outflow_weights.tif')
    outflow_direction_uri = os.path.join(
        intermediate_dir, 'outflow_directions.tif')

    _, _ = routing_cython_core.calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)

    LOGGER.info('route the sediment flux')
    #This yields sediment flux, and sediment loss which will be used for valuation

    LOGGER.info('backtrace the sediment reaching the streams')
    percent_to_sink_dataset_uri_list = [
        v_stream_uri, export_rate_uri, outflow_direction_uri, 
        outflow_weights_uri]

    aligned_dataset_uri_list = [
        raster_utils.temporary_filename() for _ in
        percent_to_sink_dataset_uri_list]

    raster_utils.align_dataset_list(
        percent_to_sink_dataset_uri_list, aligned_dataset_uri_list, 
        ["nearest", "nearest", "nearest", "nearest"], out_pixel_size, "intersection", 0)
    routing_cython_core.percent_to_sink(*(aligned_dataset_uri_list + [effective_export_to_stream_uri]))

    #multiply percent to sink with the usle
    sediment_export_dataset_list = [usle_uri, v_stream_uri, effective_export_to_stream_uri]

    usle_nodata = raster_utils.get_nodata_from_uri(usle_uri)
    v_stream_nodata = raster_utils.get_nodata_from_uri(v_stream_uri)
    export_to_stream_nodata = raster_utils.get_nodata_from_uri(effective_export_to_stream_uri)

    def export_sediment_op(usle, v_stream, export_percent):
        if usle == usle_nodata or v_stream == v_stream_nodata or export_percent == export_to_stream_nodata:
            return sed_export_nodata
        return usle * (1.0-v_stream) * export_percent
    LOGGER.info("multiplying effective export with usle and v_stream")
    sed_export_uri = os.path.join(intermediate_dir, 'sed_export.tif')
    sed_export_nodata = -1.0
    raster_utils.vectorize_datasets(
        sediment_export_dataset_list, export_sediment_op, sed_export_uri,
        gdal.GDT_Float32, sed_export_nodata, out_pixel_size, "intersection", dataset_to_align_index=0,
        aoi_uri=args['watersheds_uri'])



    #Create output shapefiles
    watershed_output_datasource_uri = os.path.join(output_dir, 'watershed_outputs.shp')
    subwatershed_output_datasource_uri = os.path.join(output_dir, 'subwatershed_outputs.shp')

    #If there is already an existing shapefile with the same name and path, delete it
    #Copy the input shapefile into the designated output folder
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_field_names = ['usle_mean', 'usle_tot', 'sed_export', 'upret_mean', 'upret_tot']

    usle_watershed = sediment_core.aggregate_raster_values(usle_uri, args['watersheds_uri'], 'sum', 'ws_id')
    LOGGER.debug(usle_watershed)

    field_summaries = {
        'ws_id': {
            'usle_mean': sediment_core.aggregate_raster_values(usle_uri, args['watersheds_uri'], 'mean', 'ws_id'),
            'usle_tot': sediment_core.aggregate_raster_values(usle_uri, args['watersheds_uri'], 'sum', 'ws_id'),
            'sed_export': sediment_core.aggregate_raster_values(sed_export_uri, args['watersheds_uri'], 'sum', 'ws_id')
#            'upret_mean': {}, 
#            'upret_tot' : {}
            },
        'subws_id': {
            'usle_mean': sediment_core.aggregate_raster_values(usle_uri, args['subwatersheds_uri'], 'mean', 'subws_id'),
            'usle_tot': sediment_core.aggregate_raster_values(usle_uri, args['subwatersheds_uri'], 'sum', 'subws_id'),
            'sed_export': sediment_core.aggregate_raster_values(sed_export_uri, args['subwatersheds_uri'], 'sum', 'subws_id')
            }
        }


    for datasource_copy_uri, original_datasource, watershed_type in [(watershed_output_datasource_uri, ogr.Open(args['watersheds_uri']), 'ws_id'),
                           (subwatershed_output_datasource_uri, ogr.Open(args['subwatersheds_uri']), 'subws_id')]:
        if os.path.isfile(datasource_copy_uri):
            os.remove(datasource_copy_uri)
        datasource_copy = esri_driver.CopyDataSource(original_datasource, datasource_copy_uri)
        layer = datasource_copy.GetLayer()
        
        for field_name in output_field_names:
            field_def = ogr.FieldDefn(field_name, ogr.OFTReal)
            layer.CreateField(field_def)
            
        #Initialize each feature field to 0.0
        for feature_id in xrange(layer.GetFeatureCount()):
            feature = layer.GetFeature(feature_id)
            for field_name in output_field_names:
                try:
                    ws_id = feature.GetFieldAsInteger(watershed_type)
                    feature.SetField(field_name, float(field_summaries[watershed_type][field_name][ws_id]))
                except KeyError:
                    feature.SetField(field_name, 0.0)
            #Save back to datasource
            layer.SetFeature(feature)

        original_datasource.Destroy()
        datasource_copy.Destroy()

    LOGGER.info('generating report')



    #TODO generate report
