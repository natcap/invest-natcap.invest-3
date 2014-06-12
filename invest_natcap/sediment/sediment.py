"""InVEST Sediment biophysical module at the "uri" level"""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr
import numpy

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import routing_cython_core

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
        args['sediment_threshold_table_uri'] - A uri to a csv that contains
            fields 'ws_id', 'dr_time', 'dr_deadvol', 'wq_annload' where 'ws_id'
            correspond to watershed input ids.
        args['sediment_valuation_table_uri'] - A uri to a csv that contains
            fields 'ws_id', 'dr_cost', 'dr_time', 'dr_disc', 'wq_cost',
            'wq_time', 'wq_disc' correspond to watershed input ids.
        args['drainage_uri'] - An optional GIS raster dataset mask, that
            indicates areas that drain to the watershed.  Format is that 1's
            indicate drainage areas and 0's or nodata indicate areas with no
            additional drainage.  This model is most accurate when the drainage
            raster aligns with the DEM.

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

    out_pixel_size = raster_utils.get_cell_size_from_uri(args['dem_uri'])

    csv_dict_reader = csv.DictReader(open(args['biophysical_table_uri'], 'rU'))
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
        [args['dem_uri']], lambda x: x.astype(numpy.float64), clipped_dem_uri,
        gdal.GDT_Float64, dem_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'],
        vectorize_op=False)

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
    v_stream_uri = os.path.join(output_dir, 'v_stream%s.tif' % file_suffix)

    routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)

    if 'drainage_uri' in args and args['drainage_uri'] != '':
        def add_drainage(stream, drainage):
            return numpy.where(drainage == 1, 1, stream)
        
        stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)
        #add additional drainage to the stream
        drainage_uri = os.path.join(output_dir, 'drainage%s.tif' % file_suffix)
        
        raster_utils.vectorize_datasets(
            [stream_uri, args['drainage_uri']], add_drainage, drainage_uri,
            gdal.GDT_Byte, stream_nodata, out_pixel_size, "intersection",
            dataset_to_align_index=0, vectorize_op=False)
        stream_uri = drainage_uri
        
    #Calculate LS term
    LOGGER.info('calculate ls term')
    ls_uri = os.path.join(intermediate_dir, 'ls%s.tif' % file_suffix)
    ls_nodata = -1.0
    calculate_ls_factor(
        flow_accumulation_uri, slope_uri, flow_direction_uri, ls_uri, ls_nodata)

    #Clip the LULC
    lulc_dataset = gdal.Open(args['landuse_uri'])
    _, lulc_nodata = raster_utils.extract_band_and_nodata(lulc_dataset)
    lulc_clipped_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [args['landuse_uri']], lambda x: x.astype(numpy.int32) , lulc_clipped_uri,
        gdal.GDT_Int32, lulc_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'],
        vectorize_op=False)
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
        return numpy.where(v_stream == 1, 0.0, retention)
    raster_utils.vectorize_datasets(
        [no_stream_retention_rate_uri, v_stream_uri], zero_out_retention_fn,
        retention_rate_uri, gdal.GDT_Float64, nodata_retention, out_pixel_size,
        "intersection", dataset_to_align_index=0,
        aoi_uri=args['watersheds_uri'], vectorize_op=False)

    LOGGER.info('building cp raster from lulc')
    lulc_to_cp_dict = dict([(lulc_code, float(table['usle_c']) * float(table['usle_p']))  for (lulc_code, table) in biophysical_table.items()])
    cp_uri = os.path.join(intermediate_dir, 'cp%s.tif' % file_suffix)
    raster_utils.reclassify_dataset(
        lulc_clipped_dataset, lulc_to_cp_dict, cp_uri, gdal.GDT_Float64,
        -1.0, exception_flag='values_required')

    LOGGER.info('calculating rkls')
    rkls_uri = os.path.join(output_dir, 'rkls%s.tif' % file_suffix)
    calculate_rkls(
        ls_uri, args['erosivity_uri'], args['erodibility_uri'], v_stream_uri,
        rkls_uri)

    LOGGER.info('calculating USLE')
    usle_uri = os.path.join(output_dir, 'usle%s.tif' % file_suffix)
    nodata_rkls = raster_utils.get_nodata_from_uri(rkls_uri)
    nodata_cp = raster_utils.get_nodata_from_uri(cp_uri)
    nodata_usle = -1.0
    def mult_rkls_cp(rkls, cp_factor, v_stream):
        return numpy.where((rkls == nodata_rkls) | (cp_factor == nodata_cp),
            nodata_usle, rkls * cp_factor * (1 - v_stream))
    raster_utils.vectorize_datasets(
        [rkls_uri, cp_uri, v_stream_uri], mult_rkls_cp, usle_uri,
        gdal.GDT_Float64, nodata_usle, out_pixel_size, "intersection",
        dataset_to_align_index=2, aoi_uri=args['watersheds_uri'],
        vectorize_op=False)

    LOGGER.info('calculating on pixel retention RKLS-USLE')
    on_pixel_retention_uri = os.path.join(
        output_dir, 'on_pixel_retention%s.tif' % file_suffix)
    on_pixel_retention_nodata = -1.0
    def sub_rkls_usle(rkls, usle):
        return numpy.where((rkls == nodata_rkls) | (usle == nodata_usle),
            nodata_usle, rkls - usle)
    raster_utils.vectorize_datasets(
        [rkls_uri, usle_uri], sub_rkls_usle, on_pixel_retention_uri,
        gdal.GDT_Float64, nodata_usle, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['watersheds_uri'],
        vectorize_op=False)

    LOGGER.info('route the sediment flux to determine upstream retention')
    #This yields sediment flux, and sediment loss which will be used for valuation
    upstream_on_pixel_retention_uri = os.path.join(
        output_dir, 'upstream_on_pixel_retention%s.tif' % file_suffix)
    sed_flux_uri = raster_utils.temporary_filename()
    routing_utils.route_flux(
        flow_direction_uri, dem_offset_uri, usle_uri, retention_rate_uri,
        upstream_on_pixel_retention_uri, sed_flux_uri, 'flux_only',
        aoi_uri=args['watersheds_uri'], stream_uri=v_stream_uri)

    sed_export_uri = os.path.join(output_dir, 'sed_export%s.tif' % file_suffix)
    percent_to_stream_uri = os.path.join(
        intermediate_dir, 'percent_to_stream%s.tif' % file_suffix)
    routing_utils.pixel_amount_exported(
        flow_direction_uri, dem_offset_uri, v_stream_uri, retention_rate_uri, 
        usle_uri, sed_export_uri, aoi_uri=args['watersheds_uri'],
        percent_to_stream_uri=percent_to_stream_uri)

    LOGGER.info('generating report')
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')

    field_summaries = {
        'usle_tot': raster_utils.aggregate_raster_values_uri(usle_uri, args['watersheds_uri'], 'ws_id').total,
        'sed_export': raster_utils.aggregate_raster_values_uri(sed_export_uri, args['watersheds_uri'], 'ws_id').total,
        'upret_tot': raster_utils.aggregate_raster_values_uri(upstream_on_pixel_retention_uri, args['watersheds_uri'], 'ws_id').total,
        }

    #Create the service field sums
    field_summaries['sed_ret_dr'] = {}
    field_summaries['sed_ret_wq'] = {}
    try:
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
    
    except KeyError as e:
        raise Exception('The sediment threshold table does not have an entry '
            'for watershed ID %d' % (ws_id))

    if 'sediment_valuation_table_uri' in args:
        sediment_valuation_table = raster_utils.get_lookup_from_csv(
            args['sediment_valuation_table_uri'], 'ws_id')
        field_summaries['sed_val_dr'] = {}
        field_summaries['sed_val_wq'] = {}
        try:
            for ws_id, value in field_summaries['upret_tot'].iteritems():
                for expense_type in ['dr', 'wq']:
                    discount = disc(sediment_valuation_table[ws_id][expense_type + '_time'],
                                    sediment_valuation_table[ws_id][expense_type + '_disc'])
                    field_summaries['sed_val_' + expense_type][ws_id] = \
                        field_summaries['sed_ret_' + expense_type][ws_id] * \
                        sediment_valuation_table[ws_id][expense_type + '_cost'] * discount
        except KeyError as e:
            raise Exception('Sediment valuation table missing watershed ID %d'
                % (ws_id))

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

    
def calculate_ls_factor(flow_accumulation_uri, slope_uri, 
                        aspect_uri, ls_factor_uri, ls_nodata):
    """Calculates the LS factor as Equation 3 from "Extension and validation 
        of a geographic information system-based method for calculating the
        Revised Universal Soil Loss Equation length-slope factor for erosion
        risk assessments in large watersheds"   

        (Required that all raster inputs are same dimensions and projections
        and have square cells)
        flow_accumulation_uri - a uri to a  single band raster of type float that
            indicates the contributing area at the inlet of a grid cell
        slope_uri - a uri to a single band raster of type float that indicates
            the slope at a pixel given as a percent
        aspect_uri - a uri to a single band raster of type float that indicates the
            direction that slopes are facing in terms of radians east and
            increase clockwise: pi/2 is north, pi is west, 3pi/2, south and
            0 or 2pi is east.
        ls_factor_uri - (input) a string to the path where the LS raster will
            be written

        returns nothing"""
    
    flow_accumulation_nodata = raster_utils.get_nodata_from_uri(
        flow_accumulation_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)
    aspect_nodata = raster_utils.get_nodata_from_uri(aspect_uri)

    #Assumes that cells are square
    cell_size = raster_utils.get_cell_size_from_uri(flow_accumulation_uri)
    cell_area = cell_size ** 2

    def ls_factor_function(aspect_angle, slope, flow_accumulation):
        """Calculate the ls factor

            aspect_angle - flow direction in radians
            slope - slope in terms of percent
            flow_accumulation - upstream pixels at this point

            returns the ls_factor calculation for this point"""

        #Skip the calculation if any of the inputs are nodata
        nodata_mask = (
            (aspect_angle == aspect_nodata) | (slope == slope_nodata) |
            (flow_accumulation == flow_accumulation_nodata))
        
        #Here the aspect direction can range from 0 to 2PI, but the purpose
        #of the term is to determine the length of the flow path on the
        #pixel, thus we take the absolute value of each trigonometric
        #function to keep the computation in the first quadrant
        xij = (numpy.abs(numpy.sin(aspect_angle)) +
            numpy.abs(numpy.cos(aspect_angle)))

        contributing_area = (flow_accumulation-1) * cell_area

        #To convert to radians, we need to divide the slope by 100 since
        #it's a percent. :(
        slope_in_radians = numpy.arctan(slope / 100.0)

        #From Equation 4 in "Extension and validation of a geographic
        #information system ..."
        slope_factor = numpy.where(slope < 9.0,
            10.8 * numpy.sin(slope_in_radians) + 0.03, 
            16.8 * numpy.sin(slope_in_radians) - 0.5)
        
        #Set the m value to the lookup table that's Table 1 in 
        #InVEST Sediment Model_modifications_10-01-2012_RS.docx in the
        #FT Team dropbox
        beta = ((numpy.sin(slope_in_radians) / 0.0896) /
            (3 * numpy.sin(slope_in_radians)**0.8 + 0.56))

        #slope table in percent
        slope_table = [1., 3.5, 5., 9.]
        exponent_table = [0.2, 0.3, 0.4, 0.5]
        #Look up the correct m value from the table
        m_exp = beta/(1+beta)
        for i in range(4):
            m_exp[slope <= slope_table[i]] = exponent_table[i]
                
        #The length part of the ls_factor:
        l_factor = (
            ((contributing_area + cell_area)**(m_exp+1) - 
             contributing_area ** (m_exp+1)) / 
            ((cell_size ** (m_exp + 2)) * (xij**m_exp) * (22.13**m_exp)))

        #From the McCool paper "as a final check against excessively long slope
        #length calculations ... cap of 333m"
        l_factor[l_factor > 333] = 333
            
        #This is the ls_factor
        return numpy.where(nodata_mask, ls_nodata, l_factor * slope_factor)
        
    #Call vectorize datasets to calculate the ls_factor
    dataset_uri_list = [aspect_uri, slope_uri, flow_accumulation_uri]
    raster_utils.vectorize_datasets(
        dataset_uri_list, ls_factor_function, ls_factor_uri, gdal.GDT_Float32,
        ls_nodata, cell_size, "intersection", dataset_to_align_index=0,
        vectorize_op=False)


def calculate_rkls(
    ls_factor_uri, erosivity_uri, erodibility_uri, stream_uri,
    rkls_uri):

    """Calculates per-pixel potential soil loss using the RKLS (revised 
        universial soil loss equation with no C or P).

        ls_factor_uri - GDAL uri with the LS factor pre-calculated
        erosivity_uri - GDAL uri with per pixel erosivity 
        erodibility_uri - GDAL uri with per pixel erodibility
        stream_uri - GDAL uri indicating locations with streams
            (0 is no stream, 1 stream)
        rkls_uri - string input indicating the path to disk
            for the resulting potential soil loss raster

        returns nothing"""

    ls_factor_nodata = raster_utils.get_nodata_from_uri(ls_factor_uri)
    erosivity_nodata = raster_utils.get_nodata_from_uri(erosivity_uri)
    erodibility_nodata = raster_utils.get_nodata_from_uri(erodibility_uri)
    stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)
    usle_nodata = -1.0

    cell_size = raster_utils.get_cell_size_from_uri(ls_factor_uri)
    cell_area_ha = cell_size ** 2 / 10000.0

    def rkls_function(ls_factor, erosivity, erodibility, v_stream):
        """Calculates the USLE equation
        
        ls_factor - length/slope factor
        erosivity - related to peak rainfall events
        erodibility - related to the potential for soil to erode
        v_stream - 1 or 0 depending if there is a stream there.  If so, no
            potential soil loss due to USLE
        
        returns ls_factor * erosivity * erodibility * usle_c_p if all arguments
            defined, nodata if some are not defined, 0 if in a stream
            (v_stream)"""

        rkls = numpy.where(
            v_stream == 1, 0.0,
            ls_factor * erosivity * erodibility * cell_area_ha)
        return numpy.where(
            (ls_factor == ls_factor_nodata) | (erosivity == erosivity_nodata) |
            (erodibility == erodibility_nodata) | (v_stream == stream_nodata),
            usle_nodata, rkls)
        
    dataset_uri_list = [
        ls_factor_uri, erosivity_uri, erodibility_uri, stream_uri]

    #Aligning with index 3 that's the stream and the most likely to be
    #aligned with LULCs
    raster_utils.vectorize_datasets(
        dataset_uri_list, rkls_function, rkls_uri, gdal.GDT_Float32,
        usle_nodata, cell_size, "intersection", dataset_to_align_index=3,
        vectorize_op=False)
