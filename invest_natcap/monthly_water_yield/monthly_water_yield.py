"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging
import csv
import re
import shutil

from osgeo import gdal
#required for py2exe to build
from scipy.sparse.csgraph import _validation

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import monthly_water_yield_cython_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('monthly_water_yield')

def execute(args):
    """Executes the Monthly Water Yield Model given the arguments in 'args'
        which are defined as follows:

        args - a Python dictionary with the following keys and values:

        args[workspace_dir] - a uri to the workspace directory where outputs
            will be written to disk
        
        args[precip_data_uri] - a uri to a CSV file that has time step data for
            precipitation
       
        args[eto_data_uri] - a uri to a CSV file that has time step data for
            ETo
        
        args[soil_max_uri] - a uri to a gdal raster for soil max
        
        args[soil_texture_uri] - a uri to a gdal raster for soil texture

        args[lulc_uri] - a URI to a gdal raster for the landuse landcover map
        
        args[lulc_data_uri] - a URI to a CSV file for the land cover code lookup
            table

        args[watersheds_uri] - a URI to an ogr shapefile of polygon geometry
            type
        
        args[sub_watersheds_uri] - a URI to an ogr shapefile of polygon geometry
            type

        args['suffix'] - a string that will be concatenated onto the
           end of file names (optional)
        
        returns - nothing
    """
    LOGGER.debug('Start Executing Model')
   
    # Set up directories for model outputs
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([workspace, intermediate_dir, output_dir])
    
    # Get input URIS
    precip_data_uri = args['precip_data_uri']
    eto_data_uri = args['eto_data_uri']
    dem_uri = args['dem_uri']
    smax_uri = args['soil_max_uri']
    soil_text_uri = args['soil_texture_uri']
    lulc_uri = args['lulc_uri']
    lulc_data_uri = args['lulc_data_uri']
    watershed_uri = args['watersheds_uri']
    model_params_uri = args['model_params_uri']
    
    # Append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
   
    # Set a flag to True if sub watersheds was provided as an input
    try:
        sub_shed_uri = args['sub_watersheds_uri']
        sub_shed_table_uri = os.path.join(
                intermediate_dir, 'sub_shed_table%s.csv' % file_suffix)
        sub_shed_present = True
    except KeyError:
        LOGGER.info('Sub Watersheds Not Provided')
        sub_shed_present = False

    # Set out_nodata value
    float_nodata = -35432.0
   
    # URIs for the impervious raster and etk raster, both based mapping lulc
    # codes to values
    imperv_area_uri = os.path.join(
            intermediate_dir, 'imperv_area%s.tif' % file_suffix)
    etk_uri = os.path.join(intermediate_dir, 'etk%s.tif' % file_suffix)
    
    for code_uri, field in zip(
            [imperv_area_uri, etk_uri],['imperv_fract', 'etk']):
        # Map the field to the lulc code in a dictionary
        lulc_code_dict = construct_lulc_lookup_dict(lulc_data_uri, field)
        # Reclassify lulc raster using lulc code to field mapping
        raster_utils.reclassify_dataset_uri(
                lulc_uri, lulc_code_dict, code_uri, gdal.GDT_Float32,
                float_nodata)

    # Get DEM WKT, Nodata, and Cell size
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(dem_uri)
    dem_nodata = raster_utils.get_nodata_from_uri(dem_uri)
    dem_cell_size = raster_utils.get_cell_size_from_uri(dem_uri)
    LOGGER.debug('DEM nodata : cellsize %s:%s', dem_nodata, dem_cell_size)

    # Create initial S_t-1 for now. Set all values to 0.0
    soil_storage_uri = os.path.join(
            intermediate_dir, 'soil_storage%s.tif' % file_suffix)
    _ = raster_utils.new_raster_from_base_uri(
            dem_uri, soil_storage_uri, 'GTIFF', float_nodata,
            gdal.GDT_Float32, fill_value=0.0)
   
    # Create a URI to hold the previous months soil storage
    prev_soil_uri = os.path.join(
            intermediate_dir, 'soil_storage_prev%s.tif' % file_suffix)

    # Calculate the slope raster from the DEM
    slope_uri = os.path.join(intermediate_dir, 'slope%s.tif' % file_suffix)
    raster_utils.calculate_slope(dem_uri, slope_uri)

    # Set up the URIs for the alpha rasters
    alpha_one_uri = os.path.join(
            intermediate_dir, 'alpha_one%s.tif' % file_suffix)
    alpha_two_uri = os.path.join(
            intermediate_dir, 'alpha_two%s.tif' % file_suffix)
    alpha_three_uri = os.path.join(
            intermediate_dir, 'alpha_three%s.tif' % file_suffix)
    alpha_uri_list = [alpha_one_uri, alpha_two_uri, alpha_three_uri]
    
    # Get the parameters and coefficients to calculate the alpha rasters
    model_param_dict = model_parameters_to_dict(model_params_uri)
    LOGGER.debug('MODEL PARAMETERS: %s', model_param_dict)
    beta = model_param_dict['beta']['beta']

    # Calculate the Alpha Rasters
    calculate_alphas(
        slope_uri, soil_text_uri, smax_uri, model_param_dict, float_nodata,
        alpha_uri_list)

    # URI for the absorption raster
    absorption_uri = os.path.join(
            intermediate_dir, 'absorption%s.tif' % file_suffix)
    # Calculate the absorption raster
    calculate_in_absorption_rate(
            imperv_area_uri, alpha_one_uri, absorption_uri, float_nodata)

    # Construct a dictionary from the precipitation time step data
    precip_data_dict = construct_time_step_data(precip_data_uri, 'p')
    LOGGER.debug('Constructed PRECIP DATA : %s', precip_data_dict)
    
    # Construct a dictionary from the ETo time step data
    eto_data_dict = construct_time_step_data(eto_data_uri, 'eto')
    LOGGER.debug('Constructed ETo DATA : %s', eto_data_dict)

    # Get a dictionary from the watershed by the id so that we can
    # have a handle on the id values for each shed
    shed_dict = raster_utils.extract_datasource_table_by_key(
            watershed_uri, 'ws_id')

    # Create individual CSV URIs for each shed based on the watershed ID's.
    # Store these URIs in a dictionary mapping to their respective shed ID's
    field_list = ['Streamflow', 'Soil Storage']    
    shed_field_list = ['Date']
    for key in shed_dict.iterkeys():
        for field in field_list:
            shed_field_list.append(field + ' ' + str(key))
    
    LOGGER.debug('Automatically Gen Field List %s', shed_field_list) 

    if sub_shed_present:
        # Get a dictionary from the sub-watershed by the id so that we can
        # have a handle on the id values for each sub-shed
        sub_shed_dict = raster_utils.extract_datasource_table_by_key(
            sub_shed_uri, 'subws_id')
        
        # Create individual CSV URIs for each sub-shed based on the watershed
        # ID's. Store these URIs in a dictionary mapping to their respective
        # sub-shed ID's
        sub_shed_field_list = ['Date']
        for key in sub_shed_dict.iterkeys():
            for field in field_list:
                sub_shed_field_list.append(field + ' ' + str(key))
        
        LOGGER.debug('Automatically Gen Sub Field List %s', sub_shed_field_list)

    # Get the keys from the time step dictionary, which will be the month/year
    # signature
    list_of_months = precip_data_dict.keys()
    # Sort the list of months taken from the precipitation dictionaries keys
    list_of_months.sort()

    # Construct resusable URIs for each month
    precip_uri = os.path.join(intermediate_dir, 'precip%s.tif' % file_suffix)
    eto_uri = os.path.join(intermediate_dir, 'eto%s.tif' % file_suffix)
    dflow_uri = os.path.join(intermediate_dir, 'dflow%s.tif' % file_suffix)
    total_precip_uri = os.path.join(
            intermediate_dir, 'total_precip%s.tif' % file_suffix)
    in_source_uri = os.path.join(
            intermediate_dir, 'in_source%s.tif' % file_suffix)
    water_uri = os.path.join(intermediate_dir, 'water_amt%s.tif' % file_suffix)
    evap_uri = os.path.join(intermediate_dir, 'evaporation%s.tif' % file_suffix)
    etc_uri = os.path.join(intermediate_dir, 'etc%s.tif' % file_suffix)
    intermed_interflow_uri = os.path.join(
            intermediate_dir, 'intermediate_interflow%s.tif' % file_suffix)
    baseflow_uri = os.path.join(
            intermediate_dir, 'baseflow%s.tif' % file_suffix)
    interflow_uri = os.path.join(
            intermediate_dir, 'interflow%s.tif' % file_suffix)
    streamflow_uri = os.path.join(
            intermediate_dir, 'streamflow%s.tif' % file_suffix)
    # Output URI for the watershed table 
    watershed_table_uri = os.path.join(
            intermediate_dir, 'wshed_table%s.csv' % file_suffix)

    # Iterate over each month, calculating the water storage and streamflow
    for cur_month in list_of_months:
        # Create a tuple for precip and eto of the current months values
        # (represented as a dictionary), the field, and uri for raster output
        precip_params = (precip_data_dict[cur_month], 'p', precip_uri)
        eto_params = (eto_data_dict[cur_month], 'eto', eto_uri)

        # For precip and eto create rasters respectively
        for data_dict, field, out_uri in [precip_params, eto_params]:
            cur_point_uri = os.path.join(intermediate_dir, 'points.shp')
            projected_point_uri = os.path.join(
                    intermediate_dir, 'proj_points.shp')
            # Since we are recycling URIs for each month clean these URIs up
            clean_uri([cur_point_uri, projected_point_uri, out_uri]) 
            # Create point shapefile from dictionary
            raster_utils.dictionary_to_point_shapefile(
                    data_dict, cur_month, cur_point_uri)

            # Project point shapefile to DEM projection
            raster_utils.reproject_datasource_uri(
                    cur_point_uri, dem_wkt, projected_point_uri) 

            # Create a new raster from the DEM to vectorize the points onto
            raster_utils.new_raster_from_base_uri(
                    dem_uri, out_uri, 'GTIFF', float_nodata, gdal.GDT_Float32,
                    fill_value=float_nodata)
            
            # Use vectorize points to construct rasters based on points and
            # fields
            raster_utils.vectorize_points_uri(
                    projected_point_uri, field, out_uri)

        # Calculate Direct Flow (Runoff) and Tp
        clean_uri([dflow_uri, total_precip_uri])
        calculate_direct_flow(
                dem_uri, precip_uri, absorption_uri, dflow_uri,
                total_precip_uri, in_source_uri, float_nodata, watershed_uri)
        
        # Calculate water amount (W)
        clean_uri([water_uri])
        calculate_water_amt(
                imperv_area_uri, total_precip_uri, alpha_one_uri, water_uri,
                float_nodata)

        # Calculate Evaporation
        clean_uri([evap_uri, etc_uri])
        calculate_evaporation(
                soil_storage_uri, smax_uri, water_uri, eto_uri, etk_uri,
                evap_uri, etc_uri, float_nodata)
        
        # Calculate Intermediate Interflow
        clean_uri([intermed_interflow_uri])
        calculate_intermediate_interflow(
                alpha_two_uri, soil_storage_uri, water_uri, evap_uri, beta,
                intermed_interflow_uri, float_nodata)

        # Calculate Baseflow
        clean_uri([baseflow_uri])
        calculate_baseflow(
                alpha_three_uri, soil_storage_uri, beta, baseflow_uri,
                float_nodata)
        
        # Calculate Final Interflow
        clean_uri([interflow_uri])
        calculate_final_interflow(
                dflow_uri, soil_storage_uri, evap_uri, baseflow_uri, smax_uri,
                water_uri, intermed_interflow_uri, interflow_uri,
                float_nodata)

        # Calculate Streamflow
        clean_uri([streamflow_uri])
        calculate_streamflow(
                dflow_uri, interflow_uri, baseflow_uri, streamflow_uri,
                float_nodata)

        # Calculate Soil Moisture for current time step, to be used as
        # previous time step in the next iteration
        clean_uri([prev_soil_uri])
        shutil.copy(soil_storage_uri, prev_soil_uri)
        clean_uri([soil_storage_uri])
        calculate_soil_stoarge(
                prev_soil_uri, water_uri, evap_uri, streamflow_uri,
                soil_storage_uri, float_nodata)

        # Dictionary to build up the outputs for the CSV tables
        out_dict = {}
        out_dict['Date'] = cur_month

        # Use Aggregate Raster function to get the max values under the
        # watersheds. For now this is what our outputs will be
        max_streamflow = raster_utils.aggregate_raster_values_uri(
                streamflow_uri, watershed_uri, 'ws_id').pixel_max
        
        max_storage = raster_utils.aggregate_raster_values_uri(
                soil_storage_uri, watershed_uri, 'ws_id').pixel_max

        LOGGER.debug('Max_streamflow dict %s', max_streamflow)
        LOGGER.debug('max_storage dict %s', max_storage)
       
        # Given the two output dictionaries build up the final dictionary that
        # will then be used to right out to the CSV
        for result_dict, field in zip(
                [max_streamflow, max_storage], field_list):
            build_csv_dict(result_dict, shed_field_list, out_dict, field)

        LOGGER.debug('OUTPUT Shed Dict: %s', out_dict)
        # Write results to the CSV
        add_row_csv_table(watershed_table_uri, shed_field_list, out_dict)

        if sub_shed_present:
            sub_out_dict = {}
            sub_out_dict['Date'] = cur_month
            
            sub_max_streamflow = raster_utils.aggregate_raster_values_uri(
                    streamflow_uri, sub_shed_uri, 'subws_id').pixel_max
            
            sub_max_storage = raster_utils.aggregate_raster_values_uri(
                    soil_storage_uri, sub_shed_uri, 'subws_id').pixel_max

            LOGGER.debug('Sub Max_streamflow dict %s', sub_max_streamflow)
            LOGGER.debug('Sub max_storage dict %s', sub_max_storage)

            # Given the two output dictionaries build up the final dictionary
            # that will then be used to right out to the CSV
            for result_dict, field in zip(
                    [sub_max_streamflow, sub_max_storage], field_list):
                build_csv_dict(
                        result_dict, sub_shed_field_list, sub_out_dict, field)

            LOGGER.debug('OUTPUT Sub Shed Dict: %s', sub_out_dict)
            # Write results to the CSV
            add_row_csv_table(
                    sub_shed_table_uri, sub_shed_field_list, sub_out_dict)

        # Move on to next month

def build_csv_dict(new_dict, columns, out_dict, field):
    """Combines a single level dictionary to an existing or non existing single
        level dicitonary
        
        new_dict - a dictionary with keys pointing to values

        columns - a list of strings
        
        out_dict - the dictionary to add the new keys and values to
        
        field - a string representing which key in 'key_list' we want to add
        
        returns - a Dictionary
    """
    for key, value in new_dict.iteritems():
        key_str = str(key)
        for col_name in columns[1:]:
            if (re.search(key_str, col_name) != None and 
                    re.match(field, col_name) != None):
                out_dict[col_name] = value
    return out_dict

def add_row_csv_table(csv_uri, column_header, single_dict):
    """Write a new row to a CSV file if it already exists or creates a new one
        with that row.

        csv_uri - a URI to a CSV file location to write to disk

        column_header - a Python list of strings representing the column headers
            for the CSV file

        single_dict - a Dictionary with keys matching the 'column_header' list,
            that point to wanted values
            example : {'Date':'01/1988', 'Sum':56, 'Mean':32}

        returns - Nothing"""
    
    csv_writer = None
    # If the file does note exist then write a new file, else append a new row
    # to the file
    if not os.path.isfile(csv_uri):
        csv_file = open(csv_uri, 'wb')

        csv_writer = csv.DictWriter(csv_file, column_header)
        # Write the columns as the first row in the table
        csv_writer.writerow(dict((fn, fn) for fn in column_header))

    else:
        # Open the CSV file in append mode 'a'. This will allow us to just tack
        # on a new row
        csv_file = open(csv_uri, 'a')
        csv_writer = csv.DictWriter(csv_file, column_header)
    
    csv_writer.writerow(single_dict)

    csv_file.close()

def clean_uri(in_uri_list):
    """Removes a file by its URI if it exists
        
        in_uri_list - a list of URIs for a file path

        returns - nothing"""

    for uri in in_uri_list:
        if os.path.isfile(uri):
            os.remove(uri)

def calculate_soil_stoarge(
        prev_soil_uri, water_uri, evap_uri, streamflow_uri, soil_storage_uri,
        out_nodata):
    """This function calculates the soil storage 

        prev_soil_uri - a URI to a gdal dataset of the previous months soil
            storage

        water_uri - a URI to a gdal datasaet for the amount of water

        evap_uri - a URI to a gdal datasaet for the evaporation

        streamflow_uri - a URI to a gdal dataset for the streamflow
        
        soil_storage_uri - a URI to a gdal dataset for the current months soil
            storage

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [prev_soil_uri, water_uri, evap_uri, streamflow_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def soil_storage_op(prev_soil_pix, water_pix, evap_pix, streamflow_pix):
        """A vectorize operation for calculating the intermediate 
            streamflow

            prev_soil_pix - a float value for the previous soil storage
            water_pix - a float value for the water amount
            evap_pix - a float value for the evap
            streamflow_pix - a float value for the streamflow
            returns - the current soil storage
        """
        for pix, pix_nodata in zip(
                [prev_soil_pix, water_pix, evap_pix, streamflow_pix],
                no_data_list):
            if pix == pix_nodata:
                return out_nodata

        return prev_soil_pix + water_pix - evap_pix - streamflow_pix

    cell_size = raster_utils.get_cell_size_from_uri(prev_soil_uri)

    raster_utils.vectorize_datasets(
            [prev_soil_uri, water_uri, evap_uri, streamflow_uri],
            soil_storage_op, soil_storage_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')

def calculate_streamflow(
        dflow_uri, interflow_uri, baseflow_uri, streamflow_uri,
        out_nodata):
    """This function calculates the streamflow 

        dflow_uri - a URI to a gdal dataset of the direct flow

        interflow_uri - a URI to a gdal datasaet for the interflow

        baseflow_uri - a URI to a gdal datasaet for the baseflow

        streamflow_uri - a URI path for the streamflow output to be
            written to disk

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [dflow_uri, interflow_uri, baseflow_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def streamflow_op(dflow_pix, interflow_pix, baseflow_pix):
        """A vectorize operation for calculating the streamflow

            dflow_pix - a float value for the direct flow
            interflow_pix - a float value for the interflow
            baseflow_pix - a float value for the baseflow

            returns - the baseflow value
        """
        for pix, pix_nodata in zip(
                [dflow_pix, interflow_pix, baseflow_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata

        return dflow_pix + interflow_pix + baseflow_pix 

    cell_size = raster_utils.get_cell_size_from_uri(dflow_uri)

    raster_utils.vectorize_datasets(
            [dflow_uri, interflow_uri, baseflow_uri], streamflow_op,
            streamflow_uri, gdal.GDT_Float32, out_nodata,
            cell_size, 'intersection')

def calculate_in_absorption_rate(
        imperv_uri, alpha_one_uri, out_uri, out_nodata):
    """This function calculates the in absorption rate to be used for
        calculating direct flow

        imperv_uri - a URI to a gdal dataset of the impervious area

        alpha_one_uri - a URI to a gdal dataset for the alpha one values
        
        out_nodata - a float for the output nodata value

        returns - nothing"""

    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [imperv_uri, alpha_one_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)
   
    def in_absorption_rate(imperv_pix, alpha_pix):
        """A vectorize operation for calculating the in absorption rate value

            imperv_pix - a float value for the impervious area in fraction
            alpha_pix - a float value for the alpha coefficients

            returns - in absorption rate value"""
        for pix, pix_nodata in zip([imperv_pix, alpha_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata
        # This equation is taken from equation (1) by factoring out the Tp value
        return imperv_pix + (1.0 - imperv_pix) * alpha_pix
    
    cell_size = raster_utils.get_cell_size_from_uri(imperv_uri)

    raster_utils.vectorize_datasets(
            [imperv_uri, alpha_one_uri], in_absorption_rate,
            out_uri, gdal.GDT_Float32, out_nodata, cell_size, 'intersection')

def calculate_final_interflow(
        dflow_uri, soil_storage_uri, evap_uri, baseflow_uri, smax_uri,
        water_uri, intermediate_interflow_uri, interflow_out_uri, out_nodata):
    """This function calculates the final interflow

        dflow_uri - a URI to a gdal dataset of the direct flow

        soil_storage_uri - a URI to a gdal datasaet for the soil water content
            from the previous time step

        evap_uri - a URI to a gdal dataset for the actual evaporation 

        baseflow_uri - a URI to a gdal dataset for the baseflow

        smax_uri - a URI to a gdal dataset for the soil water content max

        water_uri - a URI to a gdal dataset for the water avaiable on a pixel

        intermediate_interflow_uri - a URI to a gdal dataset for the
            intermediate interflow

        interflow_out_uri - a URI path for the interflow output to be written
            to disk

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [soil_storage_uri, dflow_uri, evap_uri, baseflow_uri,
            smax_uri, water_uri, intermediate_interflow_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def interflow_op(
            soil_pix, dflow_pix, evap_pix, bflow_pix, smax_pix,
            water_pix, inter_pix):
        """A vectorize operation for calculating the baseflow value

            soil_pix - a float value for the soil water content
            dflow_pix - a float value for the direct flow
            evap_pix - a float value for the actual evaporation
            bflow_pix - a float value for the baseflow
            smax_pix - a float value for the soil water content max
            water_pix - a float value for the water available
            inter_pix - a float value for the intermediate interflow

            returns - the interflow value
        """
        for pix, pix_nodata in zip(
                [soil_pix, dflow_pix, evap_pix, bflow_pix, smax_pix, water_pix,
                    inter_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata
        
        conditional = (soil_pix + water_pix - (
                    evap_pix - inter_pix - bflow_pix))

        if conditional <= smax_pix:
            return inter_pix
        else:
            return (soil_pix + water_pix - (
                        evap_pix - bflow_pix - smax_pix))

    cell_size = raster_utils.get_cell_size_from_uri(intermediate_interflow_uri)

    raster_utils.vectorize_datasets(
            [soil_storage_uri, dflow_uri, evap_uri, baseflow_uri, smax_uri,
                water_uri, intermediate_interflow_uri], interflow_op,
            interflow_out_uri, gdal.GDT_Float32, out_nodata, cell_size,
            'intersection')

def calculate_baseflow(
        alpha_three_uri, soil_storage_uri, beta, baseflow_out_uri,  out_nodata):
    """This function calculates the baseflow

        alpha_three_uri - a URI to a gdal dataset of alpha_three values

        soil_storage_uri - a URI to a gdal datasaet for the soil water content
            from the previous time step

        beta - a constant number

        baseflow_out_uri - a URI path for the baseflow output to be written
            to disk

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [alpha_three_uri, soil_storage_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def baseflow_op(alpha_pix, soil_pix):
        """A vectorize operation for calculating the baseflow value

            alpha_pix - a float value for the alpha coefficients
            soil_pix - a float value for the soil water content

            returns - the baseflow value
        """
        for pix, pix_nodata in zip([alpha_pix, soil_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata

        return alpha_pix * soil_pix**beta

    cell_size = raster_utils.get_cell_size_from_uri(alpha_three_uri)

    raster_utils.vectorize_datasets(
            [alpha_three_uri, soil_storage_uri], baseflow_op,
            baseflow_out_uri, gdal.GDT_Float32, out_nodata,
            cell_size, 'intersection')

def calculate_intermediate_interflow(
        alpha_two_uri, soil_storage_uri, water_uri, evap_uri, beta,
        interflow_out_uri,  out_nodata):
    """This function calculates the intermediate interflow

        alpha_two_uri - a URI to a gdal dataset of alpha_two values

        soil_storage_uri - a URI to a gdal datasaet for the soil water content
            from the previous time step

        water_uri - a URI to a gdal dataset for the water

        evap_uri - a URI to a gdal dataset for the actual evaporation

        beta - a constant number

        interflow_out_uri - a URI path for the intermediate interflow output to
            be written to disk

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [alpha_two_uri, soil_storage_uri, water_uri, evap_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def interflow_op(alpha_pix, soil_pix, water_pix, evap_pix):
        """A vectorize operation for calculating the interflow value

            alpha_pix - a float value for the alpha coefficients
            soil_pix - a float value for the soil water content
            water_pix - a float value for the water
            evap_pix - a float value for the actual evaporation

            returns - the interflow value
        """
        for pix, pix_nodata in zip(
                [alpha_pix, soil_pix, water_pix, evap_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata
       
        try:
            result = alpha_pix * soil_pix**beta * (
                water_pix - evap_pix * (1.0 - math.exp(
                    -1.0 * (water_pix / evap_pix))))
        except OverflowError:
            #NOTE: Talk To RICH about
            LOGGER.debug(water_pix)
            LOGGER.debug(evap_pix)
            result = 1.0

        return result

    cell_size = raster_utils.get_cell_size_from_uri(alpha_two_uri)

    raster_utils.vectorize_datasets(
            [alpha_two_uri, soil_storage_uri, water_uri, evap_uri],
            interflow_op, interflow_out_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')

def calculate_water_amt(
        imperv_area_uri, total_precip_uri, alpha_one_uri, water_out_uri,
        out_nodata):
    """Calculates the water available on a pixel

        imperv_area_uri - a URI to a gdal dataset for the impervious area in
            fraction
        total_precip_uri - a URI to a gdal dataset for the total precipiation

        alpha_one_uri - a URI to a gdal dataset of alpha_one values

        water_out_uri - a URI path for the water output to be written to disk

        out_nodata - a float for the output nodata value

        returns - nothing
    """
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [imperv_area_uri, alpha_one_uri, total_precip_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def water_op(imperv_pix, alpha_pix, precip_pix):
        """Vectorize function for computing water value
        
            imperv_pix - a float value for the impervious area in fraction
            tot_p_pix - a float value for the precipitation
            alpha_pix - a float value for the alpha variable

            returns - value for water"""
        for pix, pix_nodata in zip(
                [imperv_pix, alpha_pix, precip_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata

        return (1 - imperv_pix) * (1 - alpha_pix) * precip_pix

    cell_size = raster_utils.get_cell_size_from_uri(alpha_one_uri)

    raster_utils.vectorize_datasets(
            [imperv_area_uri, alpha_one_uri, total_precip_uri], water_op,
            water_out_uri, gdal.GDT_Float32, out_nodata, cell_size,
            'intersection')

def calculate_evaporation(
        soil_storage_uri, smax_uri, water_uri, eto_uri, etk_uri, evap_uri,
        etc_uri, out_nodata):
    """This function calculates the actual evaporation

        soil_storage_uri - a URI to a gdal dataset for the previous time steps
            soil water content
        
        smax_uri - a URI to a gdal dataset for soil maximum water content
        
        water_uri - a URI to a gdal dataset for the water available on a pixel
        
        eto_uri - a URI to a gdal dataset for the potential evapotranspiration
        
        etk_uri - a URI to a gdal dataset for the etk coefficients
        
        evap_uri - a URI path for the actual evaporation output to be
            written to disk
        
        etc_uri - a URI path for the plant specific potential
            evapotranspiration rate to be written to disk

        out_nodata - a float for the output nodata value

        returns - nothing
    """

    eto_nodata = raster_utils.get_nodata_from_uri(eto_uri)
    etk_nodata = raster_utils.get_nodata_from_uri(etk_uri)

    def etc_op(eto_pix, etk_pix):
        """Vectorize operation for calculating the plant potential
            evapotranspiration
        
            eto_pix - a float value for ETo 
            etk_pix - a float value for ETK coefficient

            returns - a float value for ETc"""

        if eto_pix == eto_nodata or etk_pix == etk_nodata:
            return out_nodata
    
        return eto_pix * etk_pix

    cell_size = raster_utils.get_cell_size_from_uri(soil_storage_uri)

    raster_utils.vectorize_datasets(
            [eto_uri, etk_uri], etc_op, etc_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')
    
    def actual_evap(water_pix, soil_pix, etc_pix, smax_pix):
        """Vectorize Operation for computing actual evaporation

            water_pix - a float for the water value
            soil_pix - a float for the soil water content value of the previous
                time step
            etc_pix - a float for the plant potential evapotranspiration rate
                value
            smax_pix - a float value for the plant available water content

            returns - the actual evaporation value
        """
        for pix, pix_nodata in zip(
                [water_pix, soil_pix, etc_pix, smax_pix], no_data_list):
            if pix == pix_nodata: 
                return out_nodata
        
        if water_pix < etc_pix:
            # NOTE: I think this is wrong, should be 1 - e^x. Check with Rich
            #return water_pix + soil_pix * math.fabs(
            #        math.expm1(-1 * ((etc_pix - water_pix) / smax_pix)))
            return water_pix + soil_pix * (
                    1.0 - math.exp((etc_pix - water_pix) / smax_pix))
        else:
            return etc_pix
    
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [water_uri, soil_storage_uri, etc_uri, smax_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)
        
    raster_utils.vectorize_datasets(
            [water_uri, soil_storage_uri, etc_uri, smax_uri], actual_evap,
            evap_uri, gdal.GDT_Float32, out_nodata, cell_size,
            'intersection')

def calculate_direct_flow(
        dem_uri, precip_uri, in_absorption_uri, dt_out_uri, tp_out_uri,
        in_source_uri, out_nodata, watershed_uri):
    """This function calculates the direct flow over the catchment
    
        dem_uri - a URI to a gdal dataset of an elevation map
        
        precip_uri - a URI to a gdal dataset of the precipitation over the
            landscape
       
        in_absorption_uri - a URI to a gdal dataset of the in absorption rate
            values

        in_source_uri - a URI path for the in source output as a gdal dataset

        dt_out_uri - a URI path for the direct flow output as a gdal dataset
        
        tp_out_uri - a URI path for the total precip output as a gdal dataset

        out_nodata - a float for the output nodata value
    
        watershed_uri - a URI to an OGR shapefile for the watershed

        returns - Nothing
    """
    no_data_list = []
    # Build up a list of nodata values to check against
    for raster_uri in [precip_uri, in_absorption_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    # CALCULATE IN_SOURCE: P(i,t) * in_absorption_rate
    def in_source_op(precip_pix, in_absorption_pix):
        """Vectorize function for computing in source value
       
           precip_pix - a float value for the precipitation amount
           in_absorption_pix - a float value for the in absorption rate

           returns - in source value"""
        for pix, pix_nodata in zip(
                [precip_pix, in_absorption_pix], no_data_list):
            if pix == pix_nodata:
                return out_nodata
        
        return precip_pix * in_absorption_pix
    
    cell_size = raster_utils.get_cell_size_from_uri(dem_uri)

    raster_utils.vectorize_datasets(
            [precip_uri, in_absorption_uri], in_source_op, in_source_uri,
            gdal.GDT_Float32, out_nodata, cell_size, 'intersection')

    temp_uri = raster_utils.temporary_filename()

    # CALCULATE ROUTE_FLUX
    routing_utils.route_flux(
        dem_uri, in_source_uri, in_absorption_uri, temp_uri, dt_out_uri,
        'source_and_flux', watershed_uri)

    #Use Dt and precip to calculate tp (Equation 2)
    monthly_water_yield_cython_core.calculate_tp(
        dem_uri, precip_uri, dt_out_uri, tp_out_uri)

def calculate_alphas(
        slope_uri, soil_text_uri, smax_uri, alpha_table, out_nodata, 
        output_uri_list):
    """Calculates and creates gdal datasets for three alpha values used in
        various equations throughout the monthly water yield model

        slope_uri - a uri to a gdal dataset for the slope
        
        soil_text_uri - a uri to a gdal dataset for the soil texture 
        
        smax_uri - a uri to a gdal dataset for the maximum soil water content
        
        alpha_table - a dictionary for the constant coefficients used in
            calculating the alpha variables
            alpha_table = {'alpha_one':{'a_one':5, 'b_one':2, 'c_one':1},
                           'alpha_two':{'a_two':2, 'b_two':5},
                           'alpha_three':{'a_three':6, 'b_three':2}}

        out_nodata - a floating point value for the output nodata

        output_uri_list - a python list of output uri's as follows:
            [alpha_one_out_uri, alpha_two_out_uri, alpha_three_out_uri]

        returns - nothing"""
    LOGGER.debug('Calculating Alpha Rasters')
    # Get the dictionaries that have the values for each alpha equation
    alpha_one = alpha_table['alpha_one'] 
    alpha_two = alpha_table['alpha_two'] 
    alpha_three = alpha_table['alpha_three'] 
    
    # Get nodata values
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)
    smax_nodata = raster_utils.get_nodata_from_uri(smax_uri)
    soil_text_nodata = raster_utils.get_nodata_from_uri(soil_text_uri)
    LOGGER.debug('Soil Text Nodata: %s', soil_text_nodata)
    slope_cell_size = raster_utils.get_cell_size_from_uri(slope_uri)
    smax_cell_size = raster_utils.get_cell_size_from_uri(smax_uri)

    def alpha_one_op(slope_pix, soil_text_pix):
        """Vectorization operation to calculate the alpha one variable used in
            equations throughout the monthly water yield model

            slope_pix - the slope value for a pixel
            soil_text_pix - the soil texture value for a pixel

            returns - out_nodata if slope_pix is a nodata value, else returns
                the alpha one value"""
        if slope_pix == slope_nodata or soil_text_pix == soil_text_nodata:
            return out_nodata
        else:
            return (alpha_one['a_one'] + (alpha_one['b_one'] * slope_pix) -
                        (alpha_one['c_one'] * soil_text_pix))

    def alpha_two_op(smax_pix):
        """Vectorization operation to calculate the alpha two variable used in
            equations throughout the monthly water yield model

            smax_pix - the soil water content maximum value for a pixel

            returns - out_nodata if smax_pix is a nodata value, else returns
                the alpha two value"""
        if smax_pix == smax_nodata:
            return out_nodata
        else:
            return (alpha_two['a_two'] * math.pow(
                smax_pix, -1 * alpha_two['b_two']))
    
    def alpha_three_op(smax_pix):
        """Vectorization operation to calculate the alpha three variable used in
            equations throughout the monthly water yield model

            smax_pix - the soil water content maximum value for a pixel

            returns - out_nodata if smax_pix is a nodata value, else returns
                the alpha three value"""
        if smax_pix == smax_nodata:
            return out_nodata
        else:
            return (alpha_three['a_three'] * math.pow(
                smax_pix, -1 * alpha_three['b_three']))

    raster_utils.vectorize_datasets(
            [slope_uri, soil_text_uri], alpha_one_op, output_uri_list[0],
            gdal.GDT_Float32, out_nodata, slope_cell_size, 'intersection')

    raster_utils.vectorize_datasets(
            [smax_uri], alpha_two_op, output_uri_list[1], gdal.GDT_Float32,
            out_nodata, smax_cell_size, 'intersection')
    
    raster_utils.vectorize_datasets(
            [smax_uri], alpha_three_op, output_uri_list[2], gdal.GDT_Float32,
            out_nodata, smax_cell_size, 'intersection')

def model_parameters_to_dict(csv_uri):
    """Build a dictionary from the model parameters CSV table

        csv_uri - a URI to a CSV file for the model parameters 

        returns - a dictionary with the following structure:
            
    """
    data_file = open(csv_uri)
    data_handler = csv.DictReader(data_file)
    
    # Make the fieldnames lowercase
    data_handler.fieldnames = [f.lower() for f in data_handler.fieldnames]
    LOGGER.debug('Lowercase Fieldnames : %s', data_handler.fieldnames)

    param_dict = {}

    for row in data_handler:
        try:
            param_dict[row['use']][row['param']] = float(row['value'])
        except KeyError:
            param_dict[row['use']] = {}
            param_dict[row['use']][row['param']] = float(row['value'])

    return param_dict

def construct_lulc_lookup_dict(lulc_data_uri, field):
    """Parse a LULC lookup CSV table and construct a dictionary mapping the LULC
        codes to the value of 'field'

        lulc_data_uri - a URI to a CSV lulc lookup table

        field - a python string for the interested field to map to

        returns - a dictionary of the mapped lulc codes to the specified field
    """
    data_file = open(lulc_data_uri)
    data_handler = csv.DictReader(data_file)
    
    # Make the fieldnames lowercase
    data_handler.fieldnames = [f.lower() for f in data_handler.fieldnames]
    LOGGER.debug('Lowercase Fieldnames : %s', data_handler.fieldnames)

    lulc_dict = {}

    for row in data_handler:
        lulc_dict[int(row['lulc'])] = float(row[field])

    return lulc_dict

def construct_time_step_data(data_uri, key_field):
    """Parse the CSV data file and construct a dictionary using the provided
        'key_field' as the keys. Each unique value under 'key_field' will 
        have a dictionary of the points and corresponding value.

        data_uri - a URI path to a CSV file that has the following headers:
            [key_field, LATI, LONG, value_field], where value_field has
            particular data for the specific point

        returns - a dictionary with the following structure as an example:
            {
                '01':{
                    0:{'date':'01','lati':'44.5','long':'-123.3','eto':'10'},
                    1:{'date':'01','lati':'44.5','long':'-123.5','eto':'5'},
                    2:{'date':'01','lati':'44.3','long':'-123.3','eto':'0'}
                    },
                '02':{
                    0:{'date':'02','lati':'44.5','long':'-123.3','eto':'10'},
                    1:{'date':'02','lati':'44.5','long':'-123.4','eto':'6'},
                    2:{'date':'02','lati':'44.6','long':'-123.5','eto':'7'}
                    }...
            }
    """
    data_file = open(data_uri)

    data_reader = csv.reader(data_file)
    data_dict = {}
    
    # The first line in the file will be the stations. We do not need any of
    # this information so returning into a throw away variable. Underscore
    # indicates the variable won't be used
    _ = data_reader.next()
    # The next line in the file will be the latitudes
    latitudes = data_reader.next()
    # The next line in the file will be the longitudes
    longitudes = data_reader.next()
   
    # All following lines will be each month with the desired data for each
    # station. Loop over each month and build up a dictionary where the
    # month/year is the key that points to an inner dictionary whose keys are
    # the indexes for the stations and whos values are dictionaries with desired
    # information
    for line in data_reader:
        month = line[0]
        data_dict[month] = {}
        for index in xrange(1, len(month)):
            data_dict[month][index] = {
                    'date':month, 'lati':latitudes[index], 
                    'long': longitudes[index], key_field:line[index]}
    
    data_file.close()
    return data_dict
