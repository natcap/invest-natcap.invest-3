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


    #Load the sediment threshold table
    sediment_threshold_table = get_watershed_lookup(
        args['sediment_threshold_table_uri'])
    sediment_valuation_table = get_watershed_lookup(
        args['sediment_valuation_table_uri'])

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
        [args['dem_uri']], float, clipped_dem_uri,
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
        [args['landuse_uri']], int, lulc_clipped_uri,
        gdal.GDT_Int32, lulc_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'])
    lulc_clipped_dataset = gdal.Open(lulc_clipped_uri)


    export_rate_uri = os.path.join(intermediate_dir, 'export_rate.tif')
    retention_rate_uri = os.path.join(intermediate_dir, 'retention_rate.tif')

    LOGGER.info('building export fraction raster from lulc')
    #dividing sediment retention by 100 since it's in the csv as a percent then subtracting 1.0 to make it export
    lulc_to_export_dict = \
        dict([(lulc_code, 1.0 - float(table['sedret_eff'])/100.0) \
                  for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_export_dict %s' % lulc_to_export_dict)
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_export_dict, export_rate_uri, gdal.GDT_Float32,
        -1.0, exception_flag='values_required')
    

    LOGGER.info('building retention fraction raster from lulc')
    #dividing sediment retention by 100 since it's in the csv as a percent then subtracting 1.0 to make it export
    lulc_to_retention_dict = \
        dict([(lulc_code, float(table['sedret_eff'])/100.0) \
                  for (lulc_code, table) in biophysical_table.items()])
    LOGGER.debug('lulc_to_retention_dict %s' % lulc_to_retention_dict)
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_retention_dict, retention_rate_uri, gdal.GDT_Float32,
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

    sink_cell_set, _ = routing_cython_core.calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)

    LOGGER.info('route the sediment flux')
    #This yields sediment flux, and sediment loss which will be used for valuation
    sed_retention_uri = os.path.join(intermediate_dir, 'sed_ret.tif')
    sed_flux_uri = os.path.join(intermediate_dir, 'sed_flux.tif')

    routing_cython_core.calculate_transport(
        outflow_direction_uri, outflow_weights_uri, sink_cell_set,
        usle_uri, retention_rate_uri, sed_retention_uri, sed_flux_uri)

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
        """Calculates sediment export from the pixel and watches for nodata"""
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

    LOGGER.info('generating report')
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')

    field_summaries = {
        'usle_mean': sediment_core.aggregate_raster_values(usle_uri, args['watersheds_uri'], 'mean', 'ws_id'),
        'usle_tot': sediment_core.aggregate_raster_values(usle_uri, args['watersheds_uri'], 'sum', 'ws_id'),
        'sed_export': sediment_core.aggregate_raster_values(sed_export_uri, args['watersheds_uri'], 'sum', 'ws_id'),
        'upret_tot': sediment_core.aggregate_raster_values(sed_retention_uri, args['watersheds_uri'], 'sum', 'ws_id'),
        'upret_mean': sediment_core.aggregate_raster_values(sed_retention_uri, args['watersheds_uri'], 'mean', 'ws_id')
        }


    #Create the service field sums
    field_summaries['sret_sm_dr'] = {}
    field_summaries['sret_sm_wq'] = {}
    for ws_id, value in field_summaries['upret_tot'].iteritems():
        #The 1.26 comes from the InVEST user's guide
        field_summaries['sret_sm_dr'][ws_id] = value - \
            sediment_threshold_table[ws_id]['dr_deadvol'] * \
            1.26 / sediment_threshold_table[ws_id]['dr_time']
        field_summaries['sret_sm_wq'][ws_id] = value - \
            sediment_threshold_table[ws_id]['wq_annload']

        #Clamp any negatives to 0
        for out_field in ['sret_sm_dr', 'sret_sm_wq']:
            if field_summaries[out_field][ws_id] < 0.0:
                field_summaries[out_field][ws_id] = 0.0
    
    #Create the service field means
    field_summaries['sret_mn_dr'] = {}
    field_summaries['sret_mn_wq'] = {}
    for ws_id, value in field_summaries['upret_tot'].iteritems():
        n_cells = field_summaries['upret_tot'][ws_id] / field_summaries['upret_mean'][ws_id]
        for out_field, sum_field in [('sret_mn_dr', 'sret_sm_dr'), ('sret_mn_wq', 'sret_sm_wq')]:
            field_summaries[out_field][ws_id] = field_summaries[sum_field][ws_id] / n_cells


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
    watershed_output_datasource_uri = os.path.join(output_dir, 'watershed_outputs.shp')
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


def get_watershed_lookup(sediment_threshold_table_uri):
    """Creates a python dictionary to look up sediment threshold values
        indexed by water id

        sediment_threshold_table_uri - a URI to a csv file containing at
            least the headers "ws_id,dr_time,dr_deadvol,wq_annload"

        returns a dictionary of the form {ws_id: 
            {dr_time: .., dr_deadvol: .., wq_annload: ...}, ...}
            depending on the values of those fields"""

    with open(sediment_threshold_table_uri, 'rU') as sediment_threshold_csv_file:
        csv_reader = csv.reader(sediment_threshold_csv_file)
        header_row = csv_reader.next()
        ws_id_index = header_row.index('ws_id')
        index_to_field = dict(zip(range(len(header_row)), header_row))

        ws_threshold_lookup = {}

        for line in csv_reader:
            ws_threshold_lookup[int(line[ws_id_index])] = \
                dict([(index_to_field[int(index)], float(value)) for index, value in zip(range(len(line)), line)])

        return ws_threshold_lookup


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
