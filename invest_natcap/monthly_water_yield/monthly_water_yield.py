"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging
import csv
import datetime
import re

from osgeo import osr
from osgeo import gdal
from osgeo import ogr
import numpy as np
#required for py2exe to build
from scipy.sparse.csgraph import _validation

from invest_natcap import raster_utils
from invest_natcap.invest_core import fileio

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('monthly_water_yield')


def execute(args):
    """Doc string for the purpose of the model and the inputs packaged in 'args'
   
        args -

        args[workspace_dir] - a uri to the workspace directory where outputs
            will be written to disk
        
        args[time_step_data] - a uri to a CSV file
        
        args[soil_max_uri] - a uri to a gdal raster for soil max
        
        args[pawc_uri] - a uri to a gdal raster for plant available water
            content

        args[lulc_uri] - a URI to a gdal raster for the landuse landcover map
        
        args[lulc_data_uri] - a URI to a CSV file for the land cover code lookup
            table

        returns - nothing
    """
    LOGGER.debug('Start Executing Model')
    
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([intermediate_dir, output_dir])

    # Get input URIS
    time_step_data_uri = args['time_step_data_uri']
    dem_uri = args['dem_uri']
    smax_uri = args['soil_max_uri']
    pawc_uri = args['pawc_uri']
    lulc_uri = args['lulc_uri']
    lulc_data_uri = args['lulc_data_uri']
   
    # Set out_nodata value
    float_nodata = float(np.finfo(np.float32).min) + 1.0
    
    # Get the impervious fraction mapping from lulc codes
    imperv_dict = construct_lulc_lookup_dict(lulc_data_uri, 'imperv_fract')
    # Reclassify lulc by impervious fraction
    imperv_area_uri = os.path.join(intermediate_dir, 'imperv_area.tif')
    raster_utils.reclassify_dataset_uri(
            lulc_uri, imperv_dict, imperv_area_uri, gdal.GDT_Float32,
            float_nodata)


    # I have yet to determine how the sandy coefficient will be provided as an
    # input, so I am just hard coding in a value for now
    sandy_sa = 0.25
    beta = 2.0

    # Get DEM WKT
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(dem_uri)

    dem_nodata = raster_utils.get_nodata_from_uri(dem_uri)
    dem_cell_size = raster_utils.get_cell_size_from_uri(dem_uri)
    LOGGER.debug('DEM nodata : cellsize %s:%s', dem_nodata, dem_cell_size)

    # Create initial S_t-1 for now
    soil_storage_uri = os.path.join(intermediate_dir, 'init_soil.tif')
    _ = raster_utils.new_raster_from_base_uri(
            dem_uri, soil_storage_uri, 'GTIFF', float_nodata,
            gdal.GDT_Float32, fill_value=0.0)

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
        slope_uri, sandy_sa, smax_uri, alpha_table, float_nodata,
        alpha_uri_list)

    # Construct a dictionary from the time step data
    data_dict = construct_time_step_data(time_step_data_uri)
    LOGGER.debug('Constructed DATA : %s', data_dict)
    
    # A list of the fields from the time step table we are interested in and
    # need.
    data_fields = ['p', 'pet']

    # Get the keys from the time step dictionary, which will be the month/year
    # signature
    list_of_months = data_dict.keys()
    # Sort the list of months chronologically. 
    list_of_months = sorted(
            list_of_months, 
            key=lambda x: datetime.datetime.strptime(x, '%m/%Y'))

    precip_uri = os.path.join(intermediate_dir, 'precip.tif')
    pet_uri = os.path.join(intermediate_dir, 'pet.tif')
    raster_uri_list = [precip_uri, pet_uri]
   
    dflow_uri = os.path.join(intermediate_dir, 'dflow.tif')
    total_precip_uri = os.path.join(intermediate_dir, 'total_precip.tif')
    water_uri = os.path.join(intermediate_dir, 'water_amt.tif')
    evap_uri = os.path.join(intermediate_dir, 'evaporation.tif')
    etc_uri = os.path.join(intermediate_dir, 'etc.tif')
    intermed_interflow_uri = os.path.join(
            intermediate_dir, 'intermediate_interflow.tif')
    baseflow_uri = os.path.join(intermediate_dir, 'baseflow.tif')

    for cur_month in list_of_months:
        # Get the dictionary for the current time step month
        cur_step_dict = data_dict[cur_month]
        # Since the time step signature has a 'slash' we need to replace it with
        # an underscore so that we don't run into issues with file naming
        cur_field_name = re.sub('\/', '_', cur_month)
        
        cur_point_uri = os.path.join(intermediate_dir, 'points.shp')
        projected_point_uri = os.path.join(intermediate_dir, 'proj_points.shp')
        clean_uri([cur_point_uri, projected_point_uri]) 
        
        # Make point shapefiles based on the current time step
        raster_utils.dictionary_to_point_shapefile(
                cur_step_dict, cur_field_name, cur_point_uri)
   
        # Project point shapefile
        raster_utils.reproject_datasource_uri(
                cur_point_uri, dem_wkt, projected_point_uri) 

        # Use vectorize points to construct rasters based on points and fields
        for field, out_uri in zip(data_fields, raster_uri_list):
            clean_uri([out_uri]) 
            
            raster_utils.new_raster_from_base_uri(
                    dem_uri, out_uri, 'GTIFF', float_nodata,
                    gdal.GDT_Float32, fill_value=float_nodata)
            
            raster_utils.vectorize_points_uri(
                    projected_point_uri, field, out_uri)

        # Calculate Direct Flow (Runoff)
        clean_uri([dflow_uri, total_precip_uri])
        calculate_direct_flow(
                imperv_area_uri, dem_uri, precip_uri, alpha_one_uri, dflow_uri,
                total_precip_uri, float_nodata)
        
        # Calculate water amount (W)
        clean_uri([water_uri])
        calculate_water_amt(
                imperv_area_uri, total_precip_uri, alpha_one_uri, water_uri,
                float_nodata)

        # Calculate Evaopration
        clean_uri([evap_uri, etc_uri])
        calculate_evaporation(
                soil_storage_uri, pawc_uri, water_uri, evap_uri, etc_uri,
                float_nodata)
        
        # Calculate Interflow
        clean_uri([intermed_interflow_uri])
        calculate_intermediate_interflow(
                alpha_two_uri, soil_storage_uri, water_uri, evap_uri, beta,
                intermed_interflow_uri, float_nodata)

        # Calculate Baseflow
        clean_uri([baseflow_uri])
        calculate_baseflow(
                alpha_three_uri, soil_storage_uri, beta, baseflow_uri,
                float_nodata)

        # Calculate Streamflow

        # Calculate Soil Moisture for current time step, to be used as previous time
        # step in the next iteration

        # Add values to output table

        # Move on to next month

def clean_uri(in_uri_list):
    """Removes a file by its URI if it exists
        
        in_uri_list - a list of URIs for a file path

        returns - nothing"""

    for uri in in_uri_list:
        if os.path.isfile(uri):
            os.remove(uri)

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

            alpha_pix - a float value for the alpha coefficients
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

    cellsize = raster_utils.get_cell_size_from_uri(intermediate_interflow_uri)

    raster_utils.vectorize_datasets(
            [soil_storage_uri, dflow_uri, evap_uri, bflow_uri, smax_uri,
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
        
        return alpha_pix * soil_pix**beta * (
                water_pix - evap_pix * (1 - math.exp(
                    -1 * (water_pix / evap_pix))))

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
        soil_storage_uri, pawc_uri, water_uri, evap_out_uri, etc_uri,
        out_nodata):
    """This function calculates the actual evaporation

        soil_storage_uri - a URI to a gdal dataset for the previous time steps
            soil water content
        
        pawc_uri - a URI to a gdal dataset for plant available water conent
        
        water_uri - a URI to a gdal dataset for the W
        
        evap_out_uri - a URI path for the actual evaporation output to be
            written to disk
        
        etc_uri - a URI path for the plant potential evapotranspiration
            rate output to be written to disk

        out_nodata - a float for the output nodata value

        returns - nothing
    """
    no_data_list = []
    for raster_uri in [soil_storage_uri, pawc_uri, water_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)

    ###################################
    # COPYING WATER RASTER AND MULTIPLYING VALUES BY .9 TO GET SOMETHING TO WORK
    # WITH. ASK RICH / YONAS HOW ETC SHOULD BE CALCULATE
    # Possible calculate ETc unless this is somehow being input
    def copy_precip(water_pix):
        if water_pix in no_data_list:
            return out_nodata
        else:
            return water_pix * 0.9
    
    cell_size = raster_utils.get_cell_size_from_uri(soil_storage_uri)

    raster_utils.vectorize_datasets(
            [water_uri], copy_precip, etc_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')
    ###################################
    
    # Calculate E
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
        
    #cell_size = raster_utils.get_cell_size_from_uri(soil_storage_uri)

    raster_utils.vectorize_datasets(
            [water_uri, soil_storage_uri, etc_uri, pawc_uri], actual_evap,
            evap_out_uri, gdal.GDT_Float32, out_nodata, cell_size,
            'intersection')

def calculate_direct_flow(
        imperv_area_uri, dem_uri, precip_uri, alpha_one_uri,  dt_out_uri,
        tp_out_uri, out_nodata):
    """This function calculates the direct flow over the catchment
    
        imperv_area_uri - a URI to a gdal dataset for the impervious area in
            fraction

        dem_uri - a URI to a gdal dataset of an elevation map
        
        precip_uri - a URI to a gdal dataset of the precipitation over the
            landscape
        
        alpha_one_uri - a URI to a gdal dataset of alpha_one values
        
        dt_out_uri - a URI path for the direct flow output as a gdal dataset
        
        tp_out_uri - a URI path for the total precip output as a gdal dataset

        out_nodata - a float for the output nodata value

        returns - Nothing
    """
    no_data_list = []
    for raster_uri in [imperv_area_uri, dem_uri,precip_uri, alpha_one_uri]:
        uri_nodata = raster_utils.get_nodata_from_uri(raster_uri)
        no_data_list.append(uri_nodata)
    
    def copy_precip(precip_pix):
        if precip_pix in no_data_list:
            return out_nodata
        else:
            return precip_pix

    def direct_flow(imperv_pix, tot_p_pix, alpha_pix):
        """Vectorize function for computing direct flow
        
            imperv_pix - a float value for the impervious area in fraction
            tot_p_pix - a float value for the precipitation
            alpha_pix - a float value for the alpha variable

            returns - direct flow"""
        for pix in [imperv_pix, alpha_pix, tot_p_pix]:
            if pix in no_data_list:
                return out_nodata
        return (imperv_pix * tot_p_pix) + (
                (1 - imperv_pix) * alpha_pix * tot_p_pix)

    cell_size = raster_utils.get_cell_size_from_uri(dem_uri)

    #raster_utils.vectorize_datasets(
    #        [imperv_area_uri, precip_uri, alpha_one_uri], direct_flow,
    #        dt_out_uri, gdal.GDT_Float32, out_nodata, cell_size,
    #        'intersection')

    raster_utils.vectorize_datasets(
            [precip_uri], copy_precip, dt_out_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')
    
    raster_utils.vectorize_datasets(
            [precip_uri], copy_precip, tp_out_uri, gdal.GDT_Float32,
            out_nodata, cell_size, 'intersection')

def calculate_alphas(
        slope_uri, sandy_sa, smax_uri, alpha_table, out_nodata, output_uri_list):
    """Calculates and creates gdal datasets for three alpha values used in
        various equations throughout the monthly water yield model

        slope_uri - a uri to a gdal dataset for the slope
        
        sandy_sa - could be a uri to a dataset, but right now just passing in a
            constant value. Need to learn more from Yonas
        
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
    slope_cell_size = raster_utils.get_cell_size_from_uri(slope_uri)
    smax_cell_size = raster_utils.get_cell_size_from_uri(smax_uri)

    def alpha_one_op(slope_pix):
        """Vectorization operation to calculate the alpha one variable used in
            equations throughout the monthly water yield model

            slope_pix - the slope value for a pixel

            returns - out_nodata if slope_pix is a nodata value, else returns
                the alpha one value"""
        if slope_pix == slope_nodata:
            return out_nodata
        else:
            return (alpha_one['a_one'] + (alpha_one['b_one'] * slope_pix) -
                        (alpha_one['c_one'] * sandy_sa))

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
            [slope_uri], alpha_one_op, output_uri_list[0], gdal.GDT_Float32,
            out_nodata, slope_cell_size, 'intersection')

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

def construct_time_step_data(data_uri):
    """Parse the CSV data file and construct a dictionary using the time step
        dates as keys. Each unique date will then have a dictionary of the
        points.

        data_uri - a URI path to a CSV file

        returns - a dictionary with the following structure:
            {
                '01/1988':{
                    0:{'date':'01/1988','lati':'44.5','long':'-123.3','p':'10'},
                    1:{'date':'01/1988','lati':'44.5','long':'-123.5','p':'5'},
                    2:{'date':'01/1988','lati':'44.3','long':'-123.3','p':'0'}
                    },
                '02/1988':{
                    0:{'date':'02/1988','lati':'44.5','long':'-123.3','p':'10'},
                    1:{'date':'02/1988','lati':'44.5','long':'-123.4','p':'6'},
                    2:{'date':'02/1988','lati':'44.6','long':'-123.5','p':'7'}
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
            data_dict[row['date']][unique_id] = row
            unique_id+=1
        except KeyError:
            # If this is a new monthly time step then set the unique_id to 0
            unique_id = 0
            # Initialize the new monthly time step
            data_dict[row['date']] = {}
            # Add the first point for the monthly time step
            data_dict[row['date']][unique_id] = row
            unique_id+=1

    data_file.close()
    return data_dict
