"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging
import csv
import datetime
import re
import shutil

from osgeo import osr
from osgeo import gdal
from osgeo import ogr
import numpy as np
#required for py2exe to build
from scipy.sparse.csgraph import _validation

from invest_natcap import raster_utils
from invest_natcap.invest_core import fileio
from invest_natcap.routing import routing_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('monthly_water_yield')


def execute(args):
    """Doc string for the purpose of the model and the inputs packaged in 'args'
   
        args -

        args[workspace_dir] - a uri to the workspace directory where outputs
            will be written to disk
        
        args[precip_data_uri] - a uri to a CSV file that has time step data for
            precipitation
       
        args[pet_data_uri] - a uri to a CSV file that has time step data for
            PET
        
        args[soil_max_uri] - a uri to a gdal raster for soil max
        
        args[pawc_uri] - a uri to a gdal raster for plant available water
            content
        
        args[soil_texture_uri] - a uri to a gdal raster for soil texture

        args[lulc_uri] - a URI to a gdal raster for the landuse landcover map
        
        args[lulc_data_uri] - a URI to a CSV file for the land cover code lookup
            table

        args[watersheds_uri] - a URI to an ogr shapefile of polygon geometry
            type
        
        args[sub_watersheds_uri] - a URI to an ogr shapefile of polygon geometry
            type

        returns - nothing
    """
    LOGGER.debug('Start Executing Model')
    
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([intermediate_dir, output_dir])
    # Get input URIS
    precip_data_uri = args['precip_data_uri']
    pet_data_uri = args['pet_data_uri']
    dem_uri = args['dem_uri']
    smax_uri = args['soil_max_uri']
    soil_text_uri = args['soil_texture_uri']
    pawc_uri = args['pawc_uri']
    lulc_uri = args['lulc_uri']
    lulc_data_uri = args['lulc_data_uri']
    watershed_uri = args['watersheds_uri']
    
    try:
        sub_shed_uri = args['sub_watersheds_uri']
        sub_shed_present = True
    except:
        LOGGER.info('Sub Watersheds Not Provided')
        sub_shed_present = False

    # Set out_nodata value
    #float_nodata = float(np.finfo(np.float32).min) + 1.0
    float_nodata = -35432.0
   
    imperv_area_uri = os.path.join(intermediate_dir, 'imperv_area.tif')
    crop_uri = os.path.join(intermediate_dir, 'crop.tif')
    
    for code_uri, field in zip(
            [imperv_area_uri, crop_uri],['imperv_fract', 'crop_fract']):
        # Map the field to the lulc code in a dictionary
        lulc_code_dict = construct_lulc_lookup_dict(lulc_data_uri, field)
        # Reclassify lulc raster using lulc code to field mapping
        raster_utils.reclassify_dataset_uri(
                lulc_uri, lulc_code_dict, code_uri, gdal.GDT_Float32,
                float_nodata)

    beta = 2.0

    # Get DEM WKT
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(dem_uri)

    dem_nodata = raster_utils.get_nodata_from_uri(dem_uri)
    dem_cell_size = raster_utils.get_cell_size_from_uri(dem_uri)
    LOGGER.debug('DEM nodata : cellsize %s:%s', dem_nodata, dem_cell_size)

    # Create initial S_t-1 for now
    soil_storage_uri = os.path.join(intermediate_dir, 'soil_storage.tif')
    _ = raster_utils.new_raster_from_base_uri(
            dem_uri, soil_storage_uri, 'GTIFF', float_nodata,
            gdal.GDT_Float32, fill_value=0.0)
    
    prev_soil_uri = os.path.join(intermediate_dir, 'soil_storage_prev.tif')

    # Calculate the slope raster from the DEM
    slope_uri = os.path.join(intermediate_dir, 'slope.tif')
    raster_utils.calculate_slope(dem_uri, slope_uri)

    # Calculate the alpha rasters
    alpha_one_uri = os.path.join(intermediate_dir, 'alpha_one.tif')
    alpha_two_uri = os.path.join(intermediate_dir, 'alpha_two.tif')
    alpha_three_uri = os.path.join(intermediate_dir, 'alpha_three.tif')
    alpha_uri_list = [alpha_one_uri, alpha_two_uri, alpha_three_uri]
    
    alpha_table = {'alpha_one':{'a_one':0.07, 'b_one':0.01, 'c_one':0.002},
                   'alpha_two':{'a_two':0.2, 'b_two':2.2},
                   'alpha_three':{'a_three':1.44, 'b_three':0.68}}

    calculate_alphas(
        slope_uri, soil_text_uri, smax_uri, alpha_table, float_nodata,
        alpha_uri_list)

    absorption_uri = os.path.join(intermediate_dir, 'absorption.tif')
    calculate_in_absorption_rate(
            imperv_area_uri, alpha_one_uri, absorption_uri, float_nodata)

    # Construct a dictionary from the precipitation time step data
    precip_data_dict = construct_time_step_data(precip_data_uri, 'date')
    LOGGER.debug('Constructed PRECIP DATA : %s', precip_data_dict)
    
    # Construct a dictionary from the time step data
    pet_data_dict = construct_time_step_data(pet_data_uri, 'date')
    LOGGER.debug('Constructed PET DATA : %s', pet_data_dict)
    pet_raster_dict = build_monthly_pets(pet_data_dict, dem_uri, float_nodata)
    LOGGER.debug(pet_raster_dict)

    # Get a dictionary from the water / sub-watershed by the id so that we can
    # have a handle on the id values for each shed / sub-shed
    shed_dict = raster_utils.extract_datasource_table_by_key(
            watershed_uri, 'ws_id')

    # Create individual CSV URIs for each shed / sub-shed based on the water /
    # sub-watershed ID's. Store these URIs in a dictionary mapping to their
    # respective shed / sub-shed ID's
    csv_shed_dict = {}
#   for key in shed_dict.iterkeys():
#       csv_uri = os.path.join(intermediate_dir, 'output_shed_'+str(key)+'.csv')
#       if os.path.isfile(csv_uri):
#           os.remove(csv_uri)
#       csv_shed_dict[key] = csv_uri
    field_list = ['Streamflow', 'Soil Storage']    
    shed_field_list = ['Date']
    for key in shed_dict.iterkeys():
        for field in field_list:
            shed_field_list.append(field + ' ' + str(key))
    
    LOGGER.debug('Automatically Gen Field List %s', shed_field_list) 

    out_dict = {}


    # Define the column header for the output CSV files
    #column_header = ['Date', 'Streamflow', 'Soil Storage']
    
    # A list of the fields from the time step table we are interested in and
    # need.
    data_field = 'p'
    # Get the keys from the time step dictionary, which will be the month/year
    # signature
    list_of_months = precip_data_dict.keys()
    # Sort the list of months chronologically. 
    list_of_months = sorted(
            list_of_months, 
            key=lambda x: datetime.datetime.strptime(x, '%m/%Y'))

    precip_uri = os.path.join(intermediate_dir, 'precip.tif')
   
    dflow_uri = os.path.join(intermediate_dir, 'dflow.tif')
    total_precip_uri = os.path.join(intermediate_dir, 'total_precip.tif')
    in_source_uri = os.path.join(intermediate_dir, 'in_source.tif')
    water_uri = os.path.join(intermediate_dir, 'water_amt.tif')
    evap_uri = os.path.join(intermediate_dir, 'evaporation.tif')
    etc_uri = os.path.join(intermediate_dir, 'etc.tif')
    intermed_interflow_uri = os.path.join(
            intermediate_dir, 'intermediate_interflow.tif')
    baseflow_uri = os.path.join(intermediate_dir, 'baseflow.tif')
    interflow_uri = os.path.join(intermediate_dir, 'interflow.tif')
    watershed_table_uri = os.path.join(intermediate_dir, 'wshed_table.csv')
    streamflow_uri = os.path.join(intermediate_dir, 'streamflow.tif')

    for cur_month in list_of_months:
        # Get the dictionary for the current time step month
        cur_step_dict = precip_data_dict[cur_month]
        # Since the time step signature has a 'slash' we need to replace it with
        # an underscore so that we don't run into issues with file naming
        cur_field_name = re.sub('\/', '_', cur_month)
        
        cur_point_uri = os.path.join(intermediate_dir, 'points.shp')
        projected_point_uri = os.path.join(intermediate_dir, 'proj_points.shp')
        clean_uri([cur_point_uri, projected_point_uri]) 
       
        LOGGER.debug('CURRENT MONTH: %s', cur_month)
        pet_month_key = cur_month[:2]
        LOGGER.debug('PET MONTH KEY: %s', pet_month_key)
        pet_uri = pet_raster_dict[pet_month_key]
    
        # Make point shapefiles based on the current time step
        raster_utils.dictionary_to_point_shapefile(
                cur_step_dict, cur_field_name, cur_point_uri)
   
        # Project point shapefile
        raster_utils.reproject_datasource_uri(
                cur_point_uri, dem_wkt, projected_point_uri) 

        # Use vectorize points to construct rasters based on points and fields
        raster_utils.new_raster_from_base_uri(
                dem_uri, precip_uri, 'GTIFF', float_nodata,
                gdal.GDT_Float32, fill_value=float_nodata)
        
        raster_utils.vectorize_points_uri(
                projected_point_uri, 'p', precip_uri)

        # Calculate Direct Flow (Runoff)
        clean_uri([dflow_uri, total_precip_uri])
        calculate_direct_flow(
                dem_uri, precip_uri, absorption_uri, dflow_uri,
                total_precip_uri, in_source_uri, float_nodata, watershed_uri)
        
        # Calculate water amount (W)
        clean_uri([water_uri])
        calculate_water_amt(
                imperv_area_uri, total_precip_uri, alpha_one_uri, water_uri,
                float_nodata)

        # Calculate Evaopration
        clean_uri([evap_uri, etc_uri])
        calculate_evaporation(
                soil_storage_uri, pawc_uri, water_uri, pet_uri, crop_uri,
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

        # Calculate Soil Moisture for current time step, to be used as previous time
        # step in the next iteration
        clean_uri([prev_soil_uri])
        shutil.copy(soil_storage_uri, prev_soil_uri)
        clean_uri([soil_storage_uri])
        calculate_soil_stoarge(
                prev_soil_uri, water_uri, evap_uri, streamflow_uri,
                soil_storage_uri, float_nodata)

        # Use Aggregate Raster function to get the max values under the
        # watersheds. For now this is what our outputs will be
        max_streamflow = raster_utils.aggregate_raster_values_uri(
                streamflow_uri, watershed_uri, 'ws_id').pixel_mean
        
        max_storage = raster_utils.aggregate_raster_values_uri(
                soil_storage_uri, watershed_uri, 'ws_id').pixel_max

        LOGGER.debug('Max_streamflow dict', max_streamflow)
        LOGGER.debug('max_storage dict', max_storage)

        for result_dict, field in zip(
                [max_streamflow, max_storage], field_list):
            out_dict = build_csv_dict(
                    result_dict, shed_field_list, out_dict, field)

        LOGGER.debug('OUTPUT Shed Dict: %s', out_dict)
        write_new_table(csv_uri, shed_field_list, out_dict)


        # For each shed / sub-shed add the corresponding output values to their
        # respective CSV file
#       for key, value in max_streamflow.iteritems():
#           # Dictionary to aggregate the output information
#           line_dict = {}
#           line_dict[key] = {}
#           # Get corresponding CSV URI
#           csv_uri = csv_shed_dict[key]
#           # Get Output values
#           streamflow = value
#           storage = max_storage[key]
#           # Build the dictionary representing the next monthly line to write
#           line_dict[key]['Date'] = cur_month
#           line_dict[key]['Soil Storage'] = storage
#           line_dict[key]['Streamflow'] = streamflow
#           # Write new line to file
#           add_monthly_line(csv_uri, column_header, line_dict)

        # Move on to next month

def build_csv_dict(value_dict, columns, out_dict, adv):
    for key, value in value_dict.iteritems:
        key_str = str(key)
        for field in columns[1:]:
            if re.search(key_str, field) != None and re.match(adv, field) != None:
                try:
                    out_dict[key][field] = value
                except KeyError:
                    out_dict[key] = {}
                    out_dict[key][field] = value
    return out_dict


def add_monthly_line(csv_uri, column_header, single_dict):
    """Write a new row to a CSV file if it already exists or creates a new one
        with that row.

        csv_uri - a URI to a CSV file location to write to

        column_header - a Python list of strings representing the column headers
            for the CSV file

        data_dict - a Dictionary with two levels, where the top level has one
            key that points to a dictionary where the fields and values live.
            The fields in the inner dictionary should match with the fields
            given in 'column_header'
            example : {0: {'Date':'01/1988', 'Sum':56, 'Mean':32}}

        returns - Nothing"""
    
    # If the file does note exist then write a new file, else append a new row
    # to the file
    if not os.path.isfile(csv_uri):
        write_new_table(csv_uri, column_header, single_dict)
    else:
        # Open the CSV file in append mode 'a'. This will allow us to just tack
        # on a new row
        csv_file = open(csv_uri, 'a')
        csv_writer = csv.DictWriter(csv_file, column_header)
        # Even though there is only one key it seems efficient to let the loop
        # do the work in getting that key
        for key, value in single_dict.iteritems():
            csv_writer.writerow(value)
        
        csv_file.close()

def write_new_table(filename, fields, data):
    """Create a new csv table from a dictionary

        filename - a URI path for the new table to be written to disk
        
        fields - a python list of the column names. The order of the fields in
            the list will be the order in how they are written. ex:
            ['id', 'precip', 'total']
        
        data - a python dictionary representing the table. The dictionary
            should be constructed with unique numerical keys that point to a
            dictionary which represents a row in the table:
            data = {0 : {'id':1, 'precip':43, 'total': 65},
                    1 : {'id':2, 'precip':65, 'total': 94}}

        returns - nothing
    """
    csv_file = open(filename, 'wb')

    # Sort the keys so that the rows are written in order
    row_keys = data.keys()
    row_keys.sort() 

    csv_writer = csv.DictWriter(csv_file, fields)
    # Write the columns as the first row in the table
    csv_writer.writerow(dict((fn,fn) for fn in fields))

    for index in row_keys:
        csv_writer.writerow(data[index])

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

        water_uri - a URI to a gdal datasaet for the water

        evap_uri - a URI to a gdal datasaet for the evaporation

        streamflow_uri - a URI to a gdal dataset for the streamflow
        
        soil_storage_uri - a URI to a gdal dataset for the current months soil
            storage

        out_nodata - a float for the output nodata value

        returns - nothing"""
    
    no_data_list = []
    for raster_uri in [prev_soil_uri, water_uri, evap_uri, streamflow_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def soil_storage_op(prev_soil_pix, water_pix, evap_pix, streamflow_pix):
        """A vectorize operation for calculating the intermediate 
            streamflow

            prev_soil_pix - a float value for the previous soil storage
            water_pix - a float value for the water
            evap_pix - a float value for the evap
            streamflow_pix - a float value for the streamflow
            returns - the current soil storage
        """
        for pix in [prev_soil_pix, water_pix, evap_pix, streamflow_pix]:
            if pix in no_data_list:
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
    for raster_uri in [dflow_uri, interflow_uri, baseflow_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def streamflow_op(dflow_pix, interflow_pix, baseflow_pix):
        """A vectorize operation for calculating the intermediate 
            streamflow

            dflow_pix - a float value for the direct flow
            interflow_pix - a float value for the interflow
            baseflow_pix - a float value for the baseflow

            returns - the baseflow value
        """
        for pix in [dflow_pix, interflow_pix, baseflow_pix]:
            if pix in no_data_list:
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
    for raster_uri in [imperv_uri, alpha_one_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)
   
    def in_absorption_rate(imperv_pix, alpha_pix):
        """A vectorize operation for calculating the in absorption rate value

            imperv_pix - a float value for the impervious area in fraction
            alpha_pix - a float value for the alpha coefficients

            returns - in absorption rate value"""
        for pix in [imperv_pix, alpha_pix]:
            if pix in no_data_list:
                return out_nodata

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
    for raster_uri in [dflow_uri, soil_storage_uri, evap_uri, baseflow_uri,
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
        for pix in [dflow_pix, soil_pix, evap_pix, bflow_pix, smax_pix,
                water_pix, inter_pix]:
            if pix in no_data_list:
                return out_nodata
        
        conditional = (
                soil_pix + water_pix - (
                    evap_pix - dflow_pix - inter_pix - bflow_pix))

        if conditional <= smax_pix:
            return inter_pix
        else:
            return (
                    soil_pix + water_pix - (
                        evap_pix - dflow_pix - bflow_pix - smax_pix))

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
    for raster_uri in [alpha_three_uri, soil_storage_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def baseflow_op(alpha_pix, soil_pix):
        """A vectorize operation for calculating the baseflow value

            alpha_pix - a float value for the alpha coefficients
            soil_pix - a float value for the soil water content

            returns - the baseflow value
        """
        for pix in [alpha_pix, soil_pix]:
            if pix in no_data_list:
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
        for pix in [alpha_pix, soil_pix, water_pix, evap_pix]:
            if pix in no_data_list:
                return out_nodata
       
        try:
            res = alpha_pix * soil_pix**beta * (
                water_pix - evap_pix * (1.0 - math.exp(
                    -1.0 * (water_pix / evap_pix))))
        except OverflowError:
            LOGGER.debug(water_pix)
            LOGGER.debug(evap_pix)
            res = 1.0

        return res

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
    for raster_uri in [imperv_area_uri, total_precip_uri, alpha_one_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def water_op(imperv_pix, alpha_pix, precip_pix):
        """Vectorize function for computing water value
        
            imperv_pix - a float value for the impervious area in fraction
            tot_p_pix - a float value for the precipitation
            alpha_pix - a float value for the alpha variable

            returns - value for water"""
        for pix in [imperv_pix, alpha_pix, precip_pix]:
            if pix in no_data_list:
                return out_nodata

        return (1 - imperv_pix) * (1 - alpha_pix) * precip_pix

    cell_size = raster_utils.get_cell_size_from_uri(alpha_one_uri)

    raster_utils.vectorize_datasets(
            [imperv_area_uri, alpha_one_uri, total_precip_uri], water_op,
            water_out_uri, gdal.GDT_Float32, out_nodata, cell_size,
            'intersection')

def calculate_evaporation(
        soil_storage_uri, pawc_uri, water_uri, pet_uri, crop_uri, evap_uri,
        etc_uri, out_nodata):
    """This function calculates the actual evaporation

        soil_storage_uri - a URI to a gdal dataset for the previous time steps
            soil water content
        
        pawc_uri - a URI to a gdal dataset for plant available water conent
        
        water_uri - a URI to a gdal dataset for the W
        
        pet_uri - a URI to a gdal dataset for the potential evapotranspiration
        
        crop_uri - a URI to a gdal dataset for the crop coefficients
        
        evap_uri - a URI path for the actual evaporation output to be
            written to disk
        
        etc_uri - a URI path for the plant specific potential
            evapotranspiration rate to be written to disk

        out_nodata - a float for the output nodata value

        returns - nothing
    """
    no_data_list = []
    for raster_uri in [soil_storage_uri, pawc_uri, water_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    def etc_op(pet_pix, crop_pix):
        """Vectorize operation for calculating the plant potential
            evapotranspiration
        
            pet_pix - a float value for PET
            crop_pix - a float value for Crop coefficient

            returns - a float value for ETc"""

        for pix in [pet_pix, crop_pix]:
            if pix in no_data_list:
                return out_nodata
    
        return pet_pix * crop_pix

    cell_size = raster_utils.get_cell_size_from_uri(soil_storage_uri)

    raster_utils.vectorize_datasets(
            [pet_uri, crop_uri], etc_op, etc_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')
    
    def actual_evap(water_pix, soil_pix, etc_pix, pawc_pix):
        """Vectorize Operation for computing actual evaporation

            water_pix - a float for the water value
            soil_pix - a float for the soil water content value of the previous
                time step
            etc_pix - a float for the plant potential evapotranspiration rate
                value
            pawc_pix - a float value for the plant available water content

            returns - the actual evaporation value
        """
        for pix in [water_pix, soil_pix, etc_pix, pawc_pix]:
            if pix in no_data_list:
                return out_nodata
        
        if water_pix < etc_pix:
            return water_pix + soil_pix * math.fabs(
                    math.expm1(-1 * ((etc_pix - water_pix) / pawc_pix)))
        else:
            return etc_pix
        
    raster_utils.vectorize_datasets(
            [water_uri, soil_storage_uri, etc_uri, pawc_uri], actual_evap,
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

        returns - Nothing
    """
    no_data_list = []
    for raster_uri in [in_absorption_uri, dem_uri, precip_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    # CALCULATE IN_SOURCE: P(i,t) * in_absorption_rate
    def in_source_op(precip_pix, in_absorption_pix):
        """Vectorize function for computing in source value
       
           precip_pix - a float value for the precipitation amount
           in_absorption_pix - a float value for the in absorption rate

           returns - in source value"""
        for pix in [precip_pix, in_absorption_pix]:
            if pix in no_data_list:
                return out_nodata
        
        return precip_pix * in_absorption_pix
    
    cell_size = raster_utils.get_cell_size_from_uri(dem_uri)

    raster_utils.vectorize_datasets(
            [precip_uri, in_absorption_uri], in_source_op, in_source_uri,
            gdal.GDT_Float32, out_nodata, cell_size, 'intersection')

    # CALCULATE ROUTE_FLUX
    temp_uri = raster_utils.temporary_filename()

    routing_utils.route_flux(
            dem_uri, in_source_uri, in_absorption_uri, temp_uri, dt_out_uri, watershed_uri)

    dflow_nodata = raster_utils.get_nodata_from_uri(dt_out_uri)
    no_data_list.append(dflow_nodata)

    # CALCULATE TOTAL PRECIP
    def total_precip_op(direct_pix, in_absorption_pix):
        """Vectorize function for computing the total precipitation value
       
           direct_pix - a float value for the direct flow
           in_absorption_pix - a float value for the in absorption rate

           returns - total precipitation value"""
        for pix in [direct_pix, in_absorption_pix]:
            if pix in no_data_list:
                return out_nodata
        
        return direct_pix / in_absorption_pix
    
    raster_utils.vectorize_datasets(
            [dt_out_uri, in_absorption_uri], total_precip_op, tp_out_uri,
            gdal.GDT_Float32, out_nodata, cell_size, 'intersection')

def calculate_alphas(
        slope_uri, soil_text_uri, smax_uri, alpha_table, out_nodata, output_uri_list):
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
    alpha_one = alpha_table['alpha_one'] 
    alpha_two = alpha_table['alpha_two'] 
    alpha_three = alpha_table['alpha_three'] 

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
            return (
                    alpha_two['a_two'] * 
                    math.pow(smax_pix, -1 * alpha_two['b_two']))
    
    def alpha_three_op(smax_pix):
        """Vectorization operation to calculate the alpha three variable used in
            equations throughout the monthly water yield model

            smax_pix - the soil water content maximum value for a pixel

            returns - out_nodata if smax_pix is a nodata value, else returns
                the alpha three value"""
        if smax_pix == smax_nodata:
            return out_nodata
        else:
            return (
                    alpha_three['a_three'] * 
                    math.pow(smax_pix, -1 * alpha_three['b_three']))

    raster_utils.vectorize_datasets(
            [slope_uri, soil_text_uri], alpha_one_op, output_uri_list[0],
            gdal.GDT_Float32, out_nodata, slope_cell_size, 'intersection')

    raster_utils.vectorize_datasets(
            [smax_uri], alpha_two_op, output_uri_list[1], gdal.GDT_Float32,
            out_nodata, smax_cell_size, 'intersection')
    
    raster_utils.vectorize_datasets(
            [smax_uri], alpha_three_op, output_uri_list[2], gdal.GDT_Float32,
            out_nodata, smax_cell_size, 'intersection')

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
                    0:{'date':'01','lati':'44.5','long':'-123.3','pet':'10'},
                    1:{'date':'01','lati':'44.5','long':'-123.5','pet':'5'},
                    2:{'date':'01','lati':'44.3','long':'-123.3','pet':'0'}
                    },
                '02':{
                    0:{'date':'02','lati':'44.5','long':'-123.3','pet':'10'},
                    1:{'date':'02','lati':'44.5','long':'-123.4','pet':'6'},
                    2:{'date':'02','lati':'44.6','long':'-123.5','pet':'7'}
                    }...
            }
    """
    data_file = open(data_uri)
    data_handler = csv.DictReader(data_file)
    
    # Make the fieldnames lowercase
    data_handler.fieldnames = [f.lower() for f in data_handler.fieldnames]
    LOGGER.debug('Lowercase Fieldnames : %s', data_handler.fieldnames)
    
    data_dict = {}
    # An ID variable that will be assigned as the unique key for the sub
    # dictionary of each time step.
    unique_id = 0

    for row in data_handler:
        # Try/except block helps to properly set each monthly time step as a
        # unique key. These monthly keys map to a sub dictionary where the
        # points for the data are held. This block trys to assign those points
        # to the sub dictionary, however if the monthly time step has not been
        # added as an outer unique key, it is created in the except block.
        try:
            # Try to assign unique point to monthly time step
            data_dict[row[key_field]][unique_id] = row
            unique_id+=1
        except KeyError:
            # If this is a new monthly time step then set the unique_id to 0
            unique_id = 0
            # Initialize the new monthly time step
            data_dict[row[key_field]] = {}
            # Add the first point for the monthly time step
            data_dict[row[key_field]][unique_id] = row
            unique_id+=1

    data_file.close()
    return data_dict
    
def build_monthly_pets(pet_data_dict, dem_uri, out_nodata):
    """Creates a raster based on point values for PET for every month of the
        year. The resulting twelve rasters will have their URI's mapped to in a
        dictionary where the key will be the month

        pet_data_dict - a python dictionary

        dem_uri - a URI to a gdal dataset to build rasters from and to project
        to

        returns - a dictionary mapping month keys to gdal URIs
    """
    
    out_wkt = raster_utils.get_dataset_projection_wkt_uri(dem_uri)
    
    raster_dict = {}
    
    for key, value in pet_data_dict.iteritems():
        tmp_points_uri = raster_utils.temporary_folder()
        tmp_shape_uri = raster_utils.temporary_folder()
        tmp_raster_uri = raster_utils.temporary_filename()
        
        if os.path.isdir(tmp_points_uri):
            LOGGER.debug('Temp File is Directory')
        # Make point shapefiles based on the current time step
        raster_utils.dictionary_to_point_shapefile(
                value, 'pet', tmp_points_uri)
   
        # Project point shapefile
        raster_utils.reproject_datasource_uri(
                tmp_points_uri, out_wkt, tmp_shape_uri) 

        # Use vectorize points to construct rasters based on points and fields
        raster_utils.new_raster_from_base_uri(
                dem_uri, tmp_raster_uri, 'GTIFF', out_nodata,
                gdal.GDT_Float32, fill_value=out_nodata)
        
        raster_utils.vectorize_points_uri(
                tmp_shape_uri, 'pet', tmp_raster_uri)
       
        raster_dict[key] = tmp_raster_uri

    return raster_dict
