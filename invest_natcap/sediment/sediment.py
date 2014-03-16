"""InVEST Sediment biophysical module at the "uri" level"""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import routing_cython_core
from invest_natcap.sediment import sediment_core


logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sediment')


def execute(args):
    """This function invokes the sediment model given
        URI inputs of files. It may write log, warning, or error messages to
        stdout.

        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['suffix'] - a string to append to any output file name (optional)
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
        args['sediment_threshold_table_uri'] - A uri to a csv that contains
            fields 'ws_id', 'dr_time', 'dr_deadvol', 'wq_annload' where 'ws_id'
            correspond to watershed input ids.
        args['sediment_valuation_table_uri'] - A uri to a csv that contains
            fields 'ws_id', 'dr_cost', 'dr_time', 'dr_disc', 'wq_cost',
            'wq_time', 'wq_disc' correspond to watershed input ids.

        returns nothing."""

    #append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
    #Load the sediment threshold table
    sediment_threshold_table = raster_utils.get_lookup_from_csv(
        args['sediment_threshold_table_uri'], 'ws_id')

    out_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])

    csv_dict_reader = csv.DictReader(open(args['biophysical_table_uri']))
    biophysical_table = {}
    for row in csv_dict_reader:
        biophysical_table[int(row['lucode'])] = row

    #Test to see if the retention, c or p values are outside of 0..1
    for table_key in ['sedret_eff', 'usle_c', 'usle_p']:
        for (lulc_code, table) in biophysical_table.iteritems():
            try:
                float_value = float(table[table_key])
                if float_value < 0 or float_value > 1:
                    raise Exception('Value should be within range 0..1 offending value table %s, lulc_code %s, value %s' % (table_key, str(lulc_code), str(float_value)))
            except ValueError as e:
                raise Exception('Value is not a floating point value within range 0..1 offending value table %s, lulc_code %s, value %s' % (table_key, str(lulc_code), table[table_key]))
        
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'output')

    #Sets up the intermediate and output directory structure for the workspace
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.info('creating directory %s', directory)
            os.makedirs(directory)

    dem_nodata = raster_utils.get_nodata_from_uri(args['dem_uri'])

    #Clip the dem and cast to a float
    clipped_dem_uri = os.path.join(intermediate_dir, 'clipped_dem.tif')
    raster_utils.vectorize_datasets(
        [args['dem_uri']], float, clipped_dem_uri,
        gdal.GDT_Float64, dem_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])

    #resolve plateaus 
    dem_offset_uri = os.path.join(intermediate_dir, 'dem_offset%s.tif' % file_suffix)    
    routing_cython_core.resolve_flat_regions_for_drainage(clipped_dem_uri, dem_offset_uri)
    
    #Calculate slope
    LOGGER.info("Calculating slope")
    slope_uri = os.path.join(intermediate_dir, 'slope%s.tif' % file_suffix)
    raster_utils.calculate_slope(dem_offset_uri, slope_uri)

    #Calculate flow accumulation
    LOGGER.info("calculating flow accumulation")
    flow_accumulation_uri = os.path.join(intermediate_dir, 'flow_accumulation%s.tif' % file_suffix)
    flow_direction_uri = os.path.join(intermediate_dir, 'flow_direction%s.tif' % file_suffix)

    routing_cython_core.flow_direction_inf(dem_offset_uri, flow_direction_uri)
    routing_utils.flow_accumulation(flow_direction_uri, dem_offset_uri, flow_accumulation_uri)
    
    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    v_stream_uri = os.path.join(intermediate_dir, 'v_stream%s.tif' % file_suffix)

    routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)

    #Calculate LS term
    LOGGER.info('calculate ls term')
    ls_uri = os.path.join(intermediate_dir, 'ls%s.tif' % file_suffix)
    ls_nodata = -1.0
    sediment_core.calculate_ls_factor(
        flow_accumulation_uri, slope_uri, flow_direction_uri, ls_uri, ls_nodata)

    #Clip the LULC
    lulc_dataset = gdal.Open(args['landuse_uri'])
    _, lulc_nodata = raster_utils.extract_band_and_nodata(lulc_dataset)
    lulc_clipped_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [args['landuse_uri']], int, lulc_clipped_uri,
        gdal.GDT_Int32, lulc_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])
    lulc_clipped_dataset = gdal.Open(lulc_clipped_uri)

    export_rate_uri = os.path.join(intermediate_dir, 'export_rate%s.tif' % file_suffix)
    retention_rate_uri = os.path.join(intermediate_dir, 'retention_rate%s.tif' % file_suffix)

    LOGGER.info('building export fraction raster from lulc')
    #dividing sediment retention by 100 since it's in the csv as a percent then subtracting 1.0 to make it export
    lulc_to_export_dict = \
        dict([(lulc_code, 1.0 - float(table['sedret_eff'])) \
                  for (lulc_code, table) in biophysical_table.items()])
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_export_dict, export_rate_uri, gdal.GDT_Float64,
        -1.0, exception_flag='values_required')
    
    LOGGER.info('building retention fraction raster from lulc')
    #dividing sediment retention by 100 since it's in the csv as a percent then subtracting 1.0 to make it export
    lulc_to_retention_dict = \
        dict([(lulc_code, float(table['sedret_eff'])) \
                  for (lulc_code, table) in biophysical_table.items()])
    
    no_stream_retention_rate_uri = raster_utils.temporary_filename()
    nodata_retention = -1.0
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_retention_dict, no_stream_retention_rate_uri, gdal.GDT_Float64,
        -1.0, exception_flag='values_required')

    def zero_out_retention_fn(retention, v_stream):
        if v_stream == 1:
            return 0.0
        return retention
    raster_utils.vectorize_datasets(
        [no_stream_retention_rate_uri, v_stream_uri], zero_out_retention_fn,
        retention_rate_uri, gdal.GDT_Float64, nodata_retention, out_pixel_size,
        "intersection", dataset_to_align_index=0,
        aoi_uri=args['watersheds_uri'])

    LOGGER.info('building cp raster from lulc')
    lulc_to_cp_dict = dict([(lulc_code, float(table['usle_c']) * float(table['usle_p']))  for (lulc_code, table) in biophysical_table.items()])
    cp_uri = os.path.join(intermediate_dir, 'cp%s.tif' % file_suffix)
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_cp_dict, cp_uri, gdal.GDT_Float64,
        -1.0, exception_flag='values_required')

    LOGGER.info('calculating rkls')
    rkls_uri = os.path.join(output_dir, 'rkls%s.tif' % file_suffix)
    sediment_core.calculate_rkls(
        ls_uri, args['erosivity_uri'], args['erodibility_uri'], v_stream_uri,
        rkls_uri)

    LOGGER.info('calculating USLE')
    usle_uri = os.path.join(output_dir, 'usle%s.tif' % file_suffix)
    nodata_rkls = raster_utils.get_nodata_from_uri(rkls_uri)
    nodata_cp = raster_utils.get_nodata_from_uri(cp_uri)
    nodata_usle = -1.0
    def mult_rkls_cp(rkls, cp_factor, v_stream):
        if rkls == nodata_rkls or cp_factor == nodata_cp:
            return nodata_usle
        return rkls * cp_factor * (1 - v_stream)
    raster_utils.vectorize_datasets(
        [rkls_uri, cp_uri, v_stream_uri], mult_rkls_cp, usle_uri,
        gdal.GDT_Float64, nodata_usle, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])

    LOGGER.info('calculating on pixel retention RKLS-USLE')
    on_pixel_retention_uri = os.path.join(
        output_dir, 'on_pixel_retention%s.tif' % file_suffix)
    on_pixel_retention_nodata = -1.0
    def sub_rkls_usle(rkls, usle):
        if rkls == nodata_rkls or usle == nodata_usle:
            return nodata_usle
        return rkls - usle
    raster_utils.vectorize_datasets(
        [rkls_uri, usle_uri], sub_rkls_usle, on_pixel_retention_uri,
        gdal.GDT_Float64, nodata_usle, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])

    LOGGER.info('route the sediment flux to determine upstream retention')
    #This yields sediment flux, and sediment loss which will be used for valuation
    upstream_on_pixel_retention_uri = os.path.join(
        output_dir, 'upstream_on_pixel_retention%s.tif' % file_suffix)
    sed_flux_uri = raster_utils.temporary_filename()
    routing_utils.route_flux(
        flow_direction_uri, dem_offset_uri, usle_uri, retention_rate_uri,
        upstream_on_pixel_retention_uri, sed_flux_uri, 'flux_only',
        aoi_uri=args['watersheds_uri'], stream_uri=v_stream_uri)

    #Calculate the retention due to per pixel retention and the cp factor
    LOGGER.info("calculating total retention (upstream + CP factor)")
    sed_retention_uri = os.path.join(output_dir, 'sed_ret%s.tif' % file_suffix)
    sed_retention_nodata = -1.0
    upstream_retention_nodata = raster_utils.get_nodata_from_uri(upstream_on_pixel_retention_uri)
    on_pixel_retention_nodata = raster_utils.get_nodata_from_uri(on_pixel_retention_uri)
    def add_upstream_and_on_pixel_retention(upstream_retention, on_pixel_retention):
        if upstream_retention == upstream_retention_nodata or on_pixel_retention == on_pixel_retention_nodata:
            return upstream_retention_nodata
        return upstream_retention #+ on_pixel_retention

    raster_utils.vectorize_datasets(
        [upstream_on_pixel_retention_uri, on_pixel_retention_uri], add_upstream_and_on_pixel_retention,
        sed_retention_uri, gdal.GDT_Float64, sed_retention_nodata,
        out_pixel_size, "intersection", dataset_to_align_index=0,
        aoi_uri=args['watersheds_uri'])

    sed_export_uri = os.path.join(output_dir, 'sed_export%s.tif' % file_suffix)
    routing_utils.pixel_amount_exported(
        flow_direction_uri, dem_offset_uri, v_stream_uri, retention_rate_uri, usle_uri, sed_export_uri, aoi_uri=args['watersheds_uri'])

    LOGGER.info('generating report')
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')

    field_summaries = {
        'usle_tot': raster_utils.aggregate_raster_values_uri(usle_uri, args['watersheds_uri'], 'ws_id').total,
        'sed_export': raster_utils.aggregate_raster_values_uri(sed_export_uri, args['watersheds_uri'], 'ws_id').total,
        'upret_tot': raster_utils.aggregate_raster_values_uri(sed_retention_uri, args['watersheds_uri'], 'ws_id').total,
        }

    #Create the service field sums
    field_summaries['sed_ret_dr'] = {}
    field_summaries['sed_ret_wq'] = {}
    for ws_id, value in field_summaries['upret_tot'].iteritems():
        #The 1.26 comes from the InVEST user's guide
        field_summaries['sed_ret_dr'][ws_id] = (value - 
            sediment_threshold_table[ws_id]['dr_deadvol'] * 
            1.26 / sediment_threshold_table[ws_id]['dr_time'])
        field_summaries['sed_ret_wq'][ws_id] = (value - 
            sediment_threshold_table[ws_id]['wq_annload'])

        #Clamp any negatives to 0
        for out_field in ['sed_ret_dr', 'sed_ret_wq']:
            if field_summaries[out_field][ws_id] < 0.0:
                field_summaries[out_field][ws_id] = 0.0
    
    if 'sediment_valuation_table_uri' in args:
        sediment_valuation_table = raster_utils.get_lookup_from_csv(
            args['sediment_valuation_table_uri'], 'ws_id')
        field_summaries['sed_val_dr'] = {}
        field_summaries['sed_val_wq'] = {}
        for ws_id, value in field_summaries['upret_tot'].iteritems():
            for expense_type in ['dr', 'wq']:
                discount = disc(sediment_valuation_table[ws_id][expense_type + '_time'],
                                sediment_valuation_table[ws_id][expense_type + '_disc'])
                field_summaries['sed_val_' + expense_type][ws_id] = \
                    field_summaries['sret_sm_' + expense_type][ws_id] * \
                    sediment_valuation_table[ws_id][expense_type + '_cost'] * discount

    original_datasource = ogr.Open(args['watersheds_uri'])
    watershed_output_datasource_uri = os.path.join(output_dir, 'watershed_outputs%s.shp' % file_suffix)
    #If there is already an existing shapefile with the same name and path, delete it
    #Copy the input shapefile into the designated output folder
    if os.path.isfile(watershed_output_datasource_uri):
        os.remove(watershed_output_datasource_uri)
    datasource_copy = esri_driver.CopyDataSource(original_datasource, watershed_output_datasource_uri)
    layer = datasource_copy.GetLayer()

    for field_name in field_summaries:
        field_def = ogr.FieldDefn(field_name, ogr.OFTReal)
        layer.CreateField(field_def)

    #Initialize each feature field to 0.0
    for feature_id in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_id)
        for field_name in field_summaries:
            try:
                ws_id = feature.GetFieldAsInteger('ws_id')
                feature.SetField(field_name, float(field_summaries[field_name][ws_id]))
            except KeyError:
                LOGGER.warning('unknown field %s' % field_name)
                feature.SetField(field_name, 0.0)
        #Save back to datasource
        layer.SetFeature(feature)

    original_datasource.Destroy()
    datasource_copy.Destroy()


def disc(years, percent_rate):
    """Calculate discount rate for a given number of years
    
        years - an integer number of years
        percent_rate - a discount rate in percent

        returns the discount rate for the number of years to use in 
            a calculation like yearly_cost * disc(years, percent_rate)"""

    discount = 0.0
    for time_index in range(int(years) - 1):
        discount += 1.0 / (1.0 + percent_rate / 100.0) ** time_index
    return discount
