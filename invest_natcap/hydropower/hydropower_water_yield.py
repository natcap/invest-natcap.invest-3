"""Module that contains the core computational components for the hydropower
    model including the water yield, water scarcity, and valuation functions"""

import logging
import os
import csv
import math

import numpy as np
from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
import hydropower_cython_core

LOGGER = logging.getLogger('hydropower_water_yield')

def execute(args):
    """Executes the hydropower/water_yield model
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexes in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape. (required)
        
        args['depth_to_root_rest_layer_uri'] - a uri to an input raster describing the 
            depth of "good" soil before reaching this restrictive layer (required)
        
        args['precipitation_uri'] - a uri to an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        
        args['pawc_uri'] - a uri to an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        
        args['eto_uri'] - a uri to an input raster describing the 
            annual average evapotranspiration value for each cell. Potential
            evapotranspiration is the potential loss of water from soil by
            both evaporation from the soil and transpiration by healthy Alfalfa
            (or grass) if sufficient water is available (mm) (required)
        
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (optional)
        
        args['biophysical_table_uri'] - a uri to an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth (mm) and Kc, which are required. 
            NOTE: these data are attributes of each LULC class rather than 
            attributes of individual cells in the raster map (required)
        
        args['seasonality_constant'] - floating point value between 1 and 10 
            corresponding to the seasonal distribution of precipitation 
            (required)
        
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
        
        args['demand_table_uri'] - a uri to an input CSV table of LULC classes,
            showing consumptive water use for each landuse / land-cover type
            (cubic meters per year) (required for water scarcity)
        
        args['hydro_calibration_table_uri'] - a  uri to an input CSV table of 
            hydropower stations with associated calibration values (required)
        
        args['valuation_table_uri'] - a uri to an input CSV table of 
            hydropower stations with the following fields (required for
            valuation):
            ('ws_id', 'time_span', 'discount', 'efficiency', 'fraction',
            'cost', 'height', 'kw_price')
           
        returns - nothing"""
        
    LOGGER.info('Starting Water Yield Core Calculations')

    # Construct folder paths
    workspace = args['workspace_dir']
    output_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([workspace, output_dir])
    
    # Get inputs from the args dictionary
    lulc_uri = args['lulc_uri']
    eto_uri = args['eto_uri']
    precip_uri = args['precipitation_uri']
    depth_to_root_rest_layer_uri = args['depth_to_root_rest_layer_uri']
    pawc_uri = args['pawc_uri']
    sub_sheds_uri = None
    if 'sub_watersheds_uri' in args and args['sub_watersheds_uri'] != '':
        sub_sheds_uri = args['sub_watersheds_uri']

    sheds_uri = args['watersheds_uri']
    seasonality_constant = float(args['seasonality_constant'])
    
    # Open/read in the csv file into a dictionary and add to arguments
    bio_dict = {}
    biophysical_table_file = open(args['biophysical_table_uri'])
    reader = csv.DictReader(biophysical_table_file)
    for row in reader:
        bio_dict[int(row['lucode'])] = {
                'Kc':float(row['Kc']), 'root_depth':float(row['root_depth'])}

    biophysical_table_file.close() 
    
    # Append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['results_suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
    
    # Paths for clipping the fractp/wyield raster to watershed polygons
    fractp_clipped_path = os.path.join(output_dir, 'fractp%s.tif' % file_suffix)
    wyield_clipped_path = os.path.join(output_dir, 'wyield%s.tif' % file_suffix)
    
    # Paths for the actual evapotranspiration rasters
    aet_path = os.path.join(output_dir, 'aet%s.tif' % file_suffix) 
    
    # Paths for the watershed and subwatershed tables
    wyield_ws_table_uri = os.path.join(
            output_dir, 'water_yield_watershed%s.csv' % file_suffix) 
    wyield_sws_table_uri = os.path.join(
            output_dir, 'water_yield_subwatershed%s.csv' % file_suffix) 
    
    # The nodata value that will be used for created output rasters
    out_nodata = - 1.0
    
    # Break the bio_dict into two separate dictionaries based on
    # Kc and root_depth fields to use for reclassifying 
    Kc_dict = {}
    root_dict = {}
    for lulc_code in bio_dict:
        Kc_dict[lulc_code] = bio_dict[lulc_code]['Kc']
        root_dict[lulc_code] = bio_dict[lulc_code]['root_depth']

    # Create Kc raster from table values to use in future calculations
    LOGGER.info("Reclassifying temp_Kc raster")
    tmp_Kc_raster_uri = raster_utils.temporary_filename()
    
    raster_utils.reclassify_dataset_uri(
            lulc_uri, Kc_dict, tmp_Kc_raster_uri, gdal.GDT_Float32,
            out_nodata)

    # Create root raster from table values to use in future calculations
    LOGGER.info("Reclassifying tmp_root raster")
    tmp_root_raster_uri = raster_utils.temporary_filename()
    
    raster_utils.reclassify_dataset_uri(
            lulc_uri, root_dict, tmp_root_raster_uri, gdal.GDT_Float32,
            out_nodata)

    # Get out_nodata values so that we can avoid any issues when running
    # operations
    Kc_nodata = raster_utils.get_nodata_from_uri(tmp_Kc_raster_uri)
    root_nodata = raster_utils.get_nodata_from_uri(tmp_root_raster_uri)
    precip_nodata = raster_utils.get_nodata_from_uri(precip_uri)
    eto_nodata = raster_utils.get_nodata_from_uri(eto_uri)
    root_rest_layer_nodata = raster_utils.get_nodata_from_uri(depth_to_root_rest_layer_uri)
    pawc_nodata = raster_utils.get_nodata_from_uri(pawc_uri)
    
    def pet_op(eto_pix, Kc_pix):
        """Vectorize operation for calculating the plant potential
            evapotranspiration
        
            eto_pix - a float value for ETo 
            Kc_pix - a float value for Kc coefficient

            returns - a float value for pet"""

        if eto_pix == eto_nodata or Kc_pix == Kc_nodata:
            return out_nodata
    
        return eto_pix * Kc_pix
    
    # Get pixel size from tmp_Kc_raster_uri which should be the same resolution
    # as LULC raster
    pixel_size = raster_utils.get_cell_size_from_uri(tmp_Kc_raster_uri)
    tmp_pet_uri = raster_utils.temporary_filename()
    
    LOGGER.debug('Calculate PET from Ref Evap times Kc')
    raster_utils.vectorize_datasets(
            [eto_uri, tmp_Kc_raster_uri], pet_op, tmp_pet_uri, gdal.GDT_Float32,
            out_nodata, pixel_size, 'intersection', aoi_uri=sheds_uri)
    
    # Dictionary of out_nodata values corresponding to values for fractp_op
    # that will help avoid any out_nodata calculation issues
    fractp_nodata_dict = {
        'Kc':Kc_nodata, 
        'eto':eto_nodata,
        'precip':precip_nodata,
        'root':root_nodata,
        'soil':root_rest_layer_nodata,
        'pawc':pawc_nodata,
        }
    
    def fractp_op(Kc, eto, precip, root, soil, pawc):
        """A wrapper function to call hydropower's cython core. Acts as a
            closure for fractp_nodata_dict, out_nodata, seasonality_constant
            """

        return hydropower_cython_core.fractp_op(
            out_nodata, seasonality_constant, 
            Kc, eto, precip, root, soil, pawc, 
            Kc_nodata, eto_nodata, precip_nodata, root_nodata, soil_nodata, pawc_nodata)
    
    # Vectorize operation
    fractp_vec = np.vectorize(fractp_op)
    
    # List of rasters to pass into the vectorized fractp operation
    raster_list = [
            tmp_Kc_raster_uri, eto_uri, precip_uri, tmp_root_raster_uri,
            depth_to_root_rest_layer_uri, pawc_uri]
    
    LOGGER.debug('Performing fractp operation')
    # Create clipped fractp_clipped raster
    raster_utils.vectorize_datasets(
            raster_list, fractp_vec, fractp_clipped_path, gdal.GDT_Float32,
            out_nodata, pixel_size, 'intersection', aoi_uri=sheds_uri)
    
    def wyield_op(fractp, precip):
        """Function that calculates the water yeild raster
        
           fractp - numpy array with the fractp raster values
           precip - numpy array with the precipitation raster values (mm)
           
           returns - water yield value (mm)"""
        
        if fractp == out_nodata or precip == precip_nodata:
            return out_nodata
        else:
            return (1.0 - fractp) * precip
    
    LOGGER.debug('Performing wyield operation')
    # Create clipped wyield_clipped raster
    raster_utils.vectorize_datasets(
            [fractp_clipped_path, precip_uri], wyield_op, wyield_clipped_path,
            gdal.GDT_Float32, out_nodata, pixel_size, 'intersection',
            aoi_uri=sheds_uri)

    # Making a copy of watershed and sub-watershed to add water yield outputs
    # to
    wyield_sheds_uri = os.path.join(
            output_dir, 'wyield_sheds%s.shp' % file_suffix)
    raster_utils.copy_datasource_uri(sheds_uri, wyield_sheds_uri)

    if sub_sheds_uri is not None:
        wyield_sub_sheds_uri = os.path.join(
                output_dir, 'wyield_sub_sheds%s.shp' % file_suffix)
        raster_utils.copy_datasource_uri(sub_sheds_uri, wyield_sub_sheds_uri)

    def aet_op(fractp, precip):
        """Function to compute the actual evapotranspiration values
        
            fractp - numpy array with the fractp raster values
            precip - numpy array with the precipitation raster values (mm)
            
            returns - actual evapotranspiration values (mm)"""
        
        # checking if fractp >= 0 because it's a value that's between 0 and 1
        # and the nodata value is a large negative number. 
        if fractp >= 0 and precip != precip_nodata:
            return fractp * precip
        else:
            return out_nodata
    
    LOGGER.debug('Performing aet operation')
    # Create clipped aet raster 
    raster_utils.vectorize_datasets(
            [fractp_clipped_path, precip_uri], aet_op, aet_path,
            gdal.GDT_Float32, out_nodata, pixel_size, 'intersection',
            aoi_uri=sheds_uri)
  
    # Get the area of the pixel to use in later calculations for volume
    wyield_pixel_area = raster_utils.get_cell_area_from_uri(wyield_clipped_path)

    if sub_sheds_uri is not None:
        # Create a list of tuples that pair up field names and raster uris so
        # that we can nicely do operations below
        sws_tuple_names_uris = [
                ('precip_mn', precip_uri),('PET_mn', tmp_pet_uri),
                ('AET_mn', aet_path), ('fractp_mn', fractp_clipped_path)]

        for key_name, rast_uri in sws_tuple_names_uris:
            # Aggregrate mean over the sub-watersheds for each uri listed in
            # 'sws_tuple_names_uri'
            key_dict = raster_utils.aggregate_raster_values_uri(
                rast_uri, sub_sheds_uri, 'subws_id',
                ignore_nodata=False).pixel_mean
            # Add aggregated values to sub-watershed shapefile under new field
            # 'key_name'
            add_dict_to_shape(
                    wyield_sub_sheds_uri, key_dict, key_name, 'subws_id')
        
        # Aggregate values for the water yield raster under the sub-watershed
        agg_wyield_tup = raster_utils.aggregate_raster_values_uri(
                wyield_clipped_path, sub_sheds_uri, 'subws_id',
                ignore_nodata=False)
        # Get the pixel mean for aggregated for water yield and the number of
        # pixels in which it aggregated over
        wyield_mean_dict = agg_wyield_tup.pixel_mean 
        hectare_mean_dict = agg_wyield_tup.hectare_mean 
        pixel_count_dict = agg_wyield_tup.n_pixels
        # Add the wyield mean and number of pixels to the shapefile
        add_dict_to_shape(
                wyield_sub_sheds_uri, wyield_mean_dict, 'wyield_mn', 'subws_id')
        add_dict_to_shape(
                wyield_sub_sheds_uri, hectare_mean_dict, 'hectare_mn',
                'subws_id')
        add_dict_to_shape(
                wyield_sub_sheds_uri, pixel_count_dict, 'num_pixels',
                'subws_id')

        # Compute the water yield volume and water yield volume per hectare. The
        # values per sub-watershed will be added as fields in the sub-watersheds
        # shapefile
        compute_water_yield_volume(wyield_sub_sheds_uri, wyield_pixel_area)
    
        # Create a dictionary that maps watersheds to sub-watersheds given the
        # watershed and sub-watershed shapefiles
        field_list_sws = [
                'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn',
                'wyield_vol']
    
        # Get a dictionary from the sub-watershed shapefiles attributes based
        # on the fields to be outputted to the CSV table
        wyield_value_dict_sws = extract_datasource_table_by_key(
                wyield_sub_sheds_uri, 'subws_id', field_list_sws)
    
        LOGGER.debug('wyield_value_dict_sws : %s', wyield_value_dict_sws)
    
        # Write sub-watershed CSV table
        write_new_table(
                wyield_sws_table_uri, field_list_sws, wyield_value_dict_sws)
    
    # Create a list of tuples that pair up field names and raster uris so that
    # we can nicely do operations below
    ws_tuple_names_uris = [
            ('precip_mn', precip_uri),('PET_mn', tmp_pet_uri),
            ('AET_mn', aet_path)]
   
    for key_name, rast_uri in ws_tuple_names_uris:
        # Aggregrate mean over the watersheds for each uri listed in
        # 'ws_tuple_names_uri'
        key_dict = raster_utils.aggregate_raster_values_uri(
            rast_uri, sheds_uri, 'ws_id', ignore_nodata=False).pixel_mean
        # Add aggregated values to watershed shapefile under new field
        # 'key_name'
        add_dict_to_shape(wyield_sheds_uri, key_dict, key_name, 'ws_id')

    # Aggregate values for the water yield raster under the watershed
    agg_wyield_tup = raster_utils.aggregate_raster_values_uri(
            wyield_clipped_path, sheds_uri, 'ws_id', ignore_nodata=False)
    # Get the pixel mean for aggregated for water yield and the number of
    # pixels in which it aggregated over
    wyield_mean_dict = agg_wyield_tup.pixel_mean 
    hectare_mean_dict = agg_wyield_tup.hectare_mean 
    pixel_count_dict = agg_wyield_tup.n_pixels
    # Add the wyield mean and number of pixels to the shapefile
    add_dict_to_shape(
            wyield_sheds_uri, wyield_mean_dict, 'wyield_mn', 'ws_id')
    add_dict_to_shape(
            wyield_sheds_uri, hectare_mean_dict, 'hectare_mn', 'ws_id')
    add_dict_to_shape(
            wyield_sheds_uri, pixel_count_dict, 'num_pixels', 'ws_id')
    
    compute_water_yield_volume(wyield_sheds_uri, wyield_pixel_area)
    
    # List of wanted fields to output in the watershed CSV table
    field_list_ws = [
            'ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 'wyield_vol']
    
    # Get a dictionary from the watershed shapefiles attributes based on the
    # fields to be outputted to the CSV table
    wyield_value_dict_ws = extract_datasource_table_by_key(
            wyield_sheds_uri, 'ws_id', field_list_ws)
    
    LOGGER.debug('wyield_value_dict_ws : %s', wyield_value_dict_ws)
    
    # Write watershed CSV table
    write_new_table(wyield_ws_table_uri, field_list_ws, wyield_value_dict_ws)
  
    # Check to see if Water Scarcity was selected to run
    water_scarcity_checked = args.pop('water_scarcity_container', False)
    if not water_scarcity_checked:
        LOGGER.debug('Water Scarcity Not Selected')
        # The rest of the function is water scarcity and valuation, so we can
        # quit now
        return

    LOGGER.info('Starting Water Scarcity')
    
    # Paths for watershed scarcity table
    scarcity_table_ws_uri = os.path.join(
            output_dir, 'water_scarcity_watershed%s.csv' % file_suffix) 
    
    # Open/read in the demand csv file into a dictionary
    demand_dict = {}
    demand_table_file = open(args['demand_table_uri'])
    reader = csv.DictReader(demand_table_file)
    for row in reader:
        demand_dict[int(row['lucode'])] = int(row['demand'])
    
    LOGGER.debug('Demand_Dict : %s', demand_dict)
    demand_table_file.close()
    
    # Open/read in the calibration csv file into a dictionary
    calib_dict = {}
    hydro_cal_table_file = open(args['hydro_calibration_table_uri'])
    reader = csv.DictReader(hydro_cal_table_file)
    for row in reader:
        calib_dict[int(row['ws_id'])] = float(row['calib'])

    LOGGER.debug('Calib_Dict : %s', calib_dict) 
    hydro_cal_table_file.close()
    
    # Making a copy of watershed to add water scarcity results to
    scarcity_sheds_uri = os.path.join(
            output_dir, 'scarcity_sheds%s.shp' % file_suffix)
    raster_utils.copy_datasource_uri(sheds_uri, scarcity_sheds_uri)
   
    # Calculate the calibrated water yield for sheds
    LOGGER.debug('Calculating CYIELD')
    calculate_cyield_vol(wyield_sheds_uri, calib_dict, scarcity_sheds_uri)
    
    # Create demand raster from table values to use in future calculations
    LOGGER.info("Reclassifying demand raster")
    tmp_demand_uri = raster_utils.temporary_filename()
    raster_utils.reclassify_dataset_uri(
            lulc_uri, demand_dict, tmp_demand_uri, gdal.GDT_Float32,
            out_nodata)
    
    # Aggregate the consumption volume over sheds using the
    # reclassfied demand raster
    LOGGER.info('Aggregating Consumption Volume and Mean')

    consump_ws = raster_utils.aggregate_raster_values_uri(
        tmp_demand_uri, sheds_uri, 'ws_id', ignore_nodata=False)
    consump_vol_dict_ws = consump_ws.total
    consump_mn_dict_ws = consump_ws.pixel_mean
    
    # Add aggregated consumption to sheds shapefiles
    add_dict_to_shape(
            scarcity_sheds_uri, consump_vol_dict_ws, 'consum_vol', 'ws_id')
    
    # Add aggregated consumption means to sheds shapefiles
    add_dict_to_shape(
            scarcity_sheds_uri, consump_mn_dict_ws, 'consum_mn', 'ws_id')
    
    # Calculate the realised water supply after consumption
    LOGGER.info('Calculating RSUPPLY')
    compute_rsupply_volume(scarcity_sheds_uri, wyield_sheds_uri)
    
    # List of wanted fields to output in the watershed CSV table
    scarcity_field_list_ws = [
            'ws_id', 'cyield_vol', 'consum_vol', 'consum_mn', 'rsupply_vl',
            'rsupply_mn']
   
    # Aggregate water yield and water scarcity fields, where we exclude the
    # first field in the scarcity list because they are duplicates already
    # in the water yield list
    field_list_ws = field_list_ws + scarcity_field_list_ws[1:]

    # Get a dictionary from the watershed shapefiles attributes based on the
    # fields to be outputted to the CSV table
    scarcity_value_dict = extract_datasource_table_by_key(
            scarcity_sheds_uri, 'ws_id', scarcity_field_list_ws)
   
    # Since we want the scarcity output to have both water yield and scarcity
    # values, combine the scarcity and water yield dictionaries 
    scarcity_dict_ws = combine_dictionaries(
            wyield_value_dict_ws, scarcity_value_dict)

    LOGGER.debug('Scarcity_dict_ws : %s', scarcity_dict_ws)
    
    # Write watershed CSV table for water scarcity
    write_new_table(scarcity_table_ws_uri, field_list_ws, scarcity_dict_ws)
    
    # Check to see if Valuation was selected to run
    valuation_checked = args.pop('valuation_container', False)
    if not valuation_checked:
        LOGGER.debug('Valuation Not Selected')
        # The rest of the function is valuation, so we can quit now
        return
        
    LOGGER.info('Starting Valuation Calculation')
    service_dir = os.path.join(workspace, 'service')
    raster_utils.create_directories([service_dir])
    
    # Paths for the watershed table
    valuation_table_ws_uri = os.path.join(
            service_dir, 'hydropower_value_watershed%s.csv' % file_suffix)
    
    # Open/read in valuation parameters from CSV file
    valuation_params = {}
    valuation_table_file = open(args['valuation_table_uri'])
    reader = csv.DictReader(valuation_table_file)
    for row in reader:
        for key, val in row.iteritems():
            try:
                row[key] = float(val)
            except ValueError:
                pass

        valuation_params[int(row['ws_id'])] = row 
    
    valuation_table_file.close()
    
    # Making a copy of watershed to add valuation results to
    valuation_sheds_uri = os.path.join(
            service_dir, 'valuation_sheds%s.shp' % file_suffix)
    raster_utils.copy_datasource_uri(sheds_uri, valuation_sheds_uri)
   
    # Compute NPV and Energy for the watersheds
    LOGGER.info('Calculating NPV/ENERGY for Sheds')
    compute_watershed_valuation(
            valuation_sheds_uri, scarcity_sheds_uri, valuation_params)
    
    # List of fields for the valuation run   
    val_field_list_ws = ['ws_id', 'hp_energy', 'hp_npv']
    
    # Get a dictionary from the watershed shapefiles attributes based on the
    # fields to be outputted to the CSV table
    valuation_dict_ws = extract_datasource_table_by_key(
            valuation_sheds_uri, 'ws_id', val_field_list_ws)
    
    # Since we want the valuation output to have water yield and scarcity
    # values also, combine the dictionaries
    hydropower_dict_ws = combine_dictionaries(
            scarcity_dict_ws, valuation_dict_ws)

    LOGGER.debug('Hydro WS Dict: %s', hydropower_dict_ws)
    
    # Aggregate water yield, water scarcity, and valuation fields, where we
    # exclude the first field in the list because they are duplicates
    field_list_ws = field_list_ws + val_field_list_ws[1:]
   
    # Generate the final CSV file
    write_new_table(valuation_table_ws_uri, field_list_ws, hydropower_dict_ws)
    
def compute_watershed_valuation(val_sheds_uri, scarcity_sheds_uri, val_dict):
    """Computes and adds the net present value and energy for the watersheds to
        an output shapefile. 

        val_sheds_uri - a URI path to an OGR shapefile for the valuation
            watershed results. Where the results will be added.

        scarcity_sheds_uri - a URI path to an OGR shapefile for the water
            scarcity watersheds. This file will have needed values from
            computing water scarcity.

        val_dict - a python dictionary that has all the valuation parameters for
            each watershed

        returns - Nothing 
    """
    val_ds = ogr.Open(val_sheds_uri, 1)
    val_layer = val_ds.GetLayer()
    
    scarcity_ds = ogr.Open(scarcity_sheds_uri)
    scarcity_layer = scarcity_ds.GetLayer()
    
    # The field names for the new attributes
    energy_field = 'hp_energy'
    npv_field = 'hp_npv'

    # Add the new fields to the shapefile
    for new_field in [energy_field, npv_field]:
        field_defn = ogr.FieldDefn(new_field, ogr.OFTReal)
        val_layer.CreateField(field_defn)

    num_features = val_layer.GetFeatureCount()
    # Iterate over the number of features (polygons)
    for feat_id in xrange(num_features):
        val_feat = val_layer.GetFeature(feat_id)
        # Get the indices for the output fields
        energy_id = val_feat.GetFieldIndex(energy_field)
        npv_id = val_feat.GetFieldIndex(npv_field)
       
        # Get the watershed ID to index into the valuation parameter dictionary
        scarcity_feat = scarcity_layer.GetFeature(feat_id)
        ws_index = scarcity_feat.GetFieldIndex('ws_id')
        ws_id = scarcity_feat.GetField(ws_index)
        # Get the rsupply volume for the watershed
        rsupply_vl_id = scarcity_feat.GetFieldIndex('rsupply_vl')
        rsupply_vl = scarcity_feat.GetField(rsupply_vl_id)
       
        # Get the valuation parameters for watershed 'ws_id'
        val_row = val_dict[ws_id]
        
        # Compute hydropower energy production (KWH)
        # This is from the equation given in the Users' Guide
        energy = val_row['efficiency'] * val_row['fraction'] * val_row['height'] * rsupply_vl * 0.00272
        
        dsum = 0
        # Divide by 100 because it is input at a percent and we need
        # decimal value
        disc = val_row['discount'] / 100
        # To calculate the summation of the discount rate term over the life 
        # span of the dam we can use a geometric series
        ratio = 1 / (1 + disc)
        dsum = (1 - math.pow(ratio, val_row['time_span'])) / (1 - ratio)
        
        npv = ((val_row['kw_price'] * energy) - val_row['cost']) * dsum

        # Get the volume field index and add value
        val_feat.SetField(energy_id, energy)
        val_feat.SetField(npv_id, npv)
        
        val_layer.SetFeature(val_feat)

def combine_dictionaries(dict_1, dict_2):
    """Add dict_2 to dict_1 and return in a new dictionary. Both input
        dictionaries have the same unique keys that point to sub dictionaries.
        Therefore, the inner dictionaries are what is being accumulated. If a
        duplicate key is present in dict_2 it will be ignored.

        dict_1 - a python dictionary with unique keys that point to dictionaries
            ex: {1: {'ws_id':1, 'vol':65},
                 2: {'ws_id':2, 'vol':34}...}
        
        dict_2 - a python dictionary with unique keys that point to dictionaries
            ex: {1: {'ws_id':1, 'area':5},
                 2: {'ws_id':2, 'area':41}...}

        returns - a python dictionary with the same unique keys but updated
        inner dictionaries. ex:
            ex: {1: {'ws_id':1, 'vol':65, 'area':5},
                 2: {'ws_id':2, 'vol':34, 'area':41}...}
    """
    # Make a copy of dict_1 the dictionary we want to add on to
    dict_3 = dict_1.copy()
    # Iterate through dict_2, the dictionary we want to get new fields/values
    # from
    for key, sub_dict in dict_2.iteritems():
        # Iterate over the inner dictionary for each key
        for field, value in sub_dict.iteritems():
            # Ignore fields that already exist in dictionary we are adding to
            if not field in dict_3[key].keys():
                dict_3[key][field] = value

    return dict_3

def compute_rsupply_volume(scarcity_sheds_uri, wyield_sheds_uri):
    """Calculate the total realized water supply volume and the mean realized
        water supply volume per hectare for the given sheds (either for
        each sub-watershed or watershed). Output units in cubic meters and cubic
        meters per hectare respectively.

        scarcity_sheds_uri - a URI path to an OGR shapefile to get consumption
            values from, as well as to write out results to

        wyield_sheds_uri - a URI path to an OGR shapefile to get water yield
            values from

        returns - Nothing"""
    wyield_ds = ogr.Open(wyield_sheds_uri)
    wyield_layer = wyield_ds.GetLayer()
    
    scarcity_ds = ogr.Open(scarcity_sheds_uri, 1)
    scarcity_layer = scarcity_ds.GetLayer()
    
    # The field names for the new attributes
    rsupply_vol_name = 'rsupply_vl'
    rsupply_mn_name = 'rsupply_mn'

    # Add the new fields to the shapefile
    for new_field in [rsupply_vol_name, rsupply_mn_name]:
        field_defn = ogr.FieldDefn(new_field, ogr.OFTReal)
        scarcity_layer.CreateField(field_defn)

    num_features = wyield_layer.GetFeatureCount()
    # Iterate over the number of features (polygons)
    for feat_id in xrange(num_features):
        wyield_feat = wyield_layer.GetFeature(feat_id)
        # Get mean water yield value
        wyield_mn_id = wyield_feat.GetFieldIndex('wyield_mn')
        wyield_mn = wyield_feat.GetField(wyield_mn_id)
        
        scarcity_feat = scarcity_layer.GetFeature(feat_id)
        # Get water demand/consumption values
        cyield_id = scarcity_feat.GetFieldIndex('cyield_vol')
        cyield = scarcity_feat.GetField(cyield_id)
        consump_vol_id = scarcity_feat.GetFieldIndex('consum_vol')
        consump_vol = scarcity_feat.GetField(consump_vol_id)
        consump_mn_id = scarcity_feat.GetFieldIndex('consum_mn')
        consump_mn = scarcity_feat.GetField(consump_mn_id)
      
        # Calculate realized supply
        rsupply_vol = cyield - consump_vol
        rsupply_mn = wyield_mn - consump_mn

        # Get the indices for the output fields and set their values
        rsupply_vol_index = scarcity_feat.GetFieldIndex(rsupply_vol_name)
        scarcity_feat.SetField(rsupply_vol_index, rsupply_vol)
        rsupply_mn_index = scarcity_feat.GetFieldIndex(rsupply_mn_name)
        scarcity_feat.SetField(rsupply_mn_index, rsupply_mn)
        
        scarcity_layer.SetFeature(scarcity_feat)

def calculate_cyield_vol(
        wyield_shed_uri, calib_dict, scarcity_shed_uri):
    """Calculate the calibrated water yield volume for per sub-watershed or
        watershed, depending on inputs.

        wyield_shed_uri - a URI path to an OGR shapefile that has water yield
            values

        calib_dict - a python dictionary that has the calibrated values for the
            sheds

        scarcity_shed_uri - a URI path to an OGR shapefile to write the results
            to

        returns nothing"""
    
    wyield_ds = ogr.Open(wyield_shed_uri)
    wyield_layer = wyield_ds.GetLayer()
   
    scarcity_ds = ogr.Open(scarcity_shed_uri, 1)
    scarcity_layer = scarcity_ds.GetLayer()
    
    # The field names for the new attributes
    cyield_name = 'cyield_vol'

    # Add the new fields to the shapefile
    field_defn = ogr.FieldDefn(cyield_name, ogr.OFTReal)
    scarcity_layer.CreateField(field_defn)

    num_features = wyield_layer.GetFeatureCount()
    # Iterate over the number of features (polygons)
    for feat_id in xrange(num_features):
        wyield_feat = wyield_layer.GetFeature(feat_id)
        # Get the water yield volume
        wyield_vol_id = wyield_feat.GetFieldIndex('wyield_vol')
        wyield_vol = wyield_feat.GetField(wyield_vol_id)
        
        # Get the watershed ID
        ws_id_index = wyield_feat.GetFieldIndex('ws_id')
        ws_id = wyield_feat.GetField(ws_id_index)
        
        # Calculate calibrated water yield
        cyield_vol = wyield_vol * calib_dict[ws_id]

        scarcity_feat = scarcity_layer.GetFeature(feat_id)
        # Add calibrated water yield to feature
        scarcity_cyield_id = scarcity_feat.GetFieldIndex('cyield_vol')
        scarcity_feat.SetField(scarcity_cyield_id, cyield_vol)
        
        scarcity_layer.SetFeature(scarcity_feat)

def extract_datasource_table_by_key(
        datasource_uri, key_field, wanted_list):
    """Create a dictionary lookup table of the features in the attribute table
        of the datasource referenced by datasource_uri.

        datasource_uri - a uri to an OGR datasource
        key_field - a field in datasource_uri that refers to a key (unique) value
            for each row; for example, a polygon id.
        wanted_list - a list of field names to add to the dictionary. This is
            helpful if there are fields that are not wanted to be returned

        returns a dictionary of the form {key_field_0: 
            {field_0: value0, field_1: value1}...}"""

    # Pull apart the datasource
    datasource = ogr.Open(datasource_uri)
    layer = datasource.GetLayer()
    layer_def = layer.GetLayerDefn()

    # Build up a list of field names for the datasource table
    field_names = []
    for field_id in xrange(layer_def.GetFieldCount()):
        field_def = layer_def.GetFieldDefn(field_id)
        field_names.append(field_def.GetName())

    # Loop through each feature and build up the dictionary representing the
    # attribute table
    attribute_dictionary = {}
    for feature_index in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_index)
        feature_fields = {}
        for field_name in field_names:
            if field_name in wanted_list:
                feature_fields[field_name] = feature.GetField(field_name)
        key_value = feature.GetField(key_field)
        attribute_dictionary[key_value] = feature_fields

    return attribute_dictionary
    
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

    #  Sort the keys so that the rows are written in order
    row_keys = data.keys()
    row_keys.sort()    

    csv_writer = csv.DictWriter(csv_file, fields)
    #  Write the columns as the first row in the table
    csv_writer.writerow(dict((fn, fn) for fn in fields))

    # Write the rows from the dictionary
    for index in row_keys:
        csv_writer.writerow(data[index])

    csv_file.close()

def compute_water_yield_volume(shape_uri, pixel_area):
    """Calculate the water yield volume per sub-watershed or watershed and
        the water yield volume per hectare per sub-watershed or watershed.
        Add results to shape_uri, units are cubic meters

        shape_uri - a URI path to an ogr datasource for the sub-watershed
            or watershed shapefile. This shapefiles features should have a
            'wyield_mn' attribute, which calculations are derived from
        
        pixel_area - the area in meters squared of a pixel from the wyield
            raster. 

        returns - Nothing"""
    shape = ogr.Open(shape_uri, 1)
    layer = shape.GetLayer()
    
    # The field names for the new attributes
    vol_name = 'wyield_vol'
    ha_name = 'wyield_ha'

    # Add the new fields to the shapefile
    for new_field in [vol_name, ha_name]:
        field_defn = ogr.FieldDefn(new_field, ogr.OFTReal)
        layer.CreateField(field_defn)

    num_features = layer.GetFeatureCount()
    # Iterate over the number of features (polygons) and compute volume
    for feat_id in xrange(num_features):
        feat = layer.GetFeature(feat_id)
        wyield_mn_id = feat.GetFieldIndex('wyield_mn')
        wyield_mn = feat.GetField(wyield_mn_id)
        hectare_mn_id = feat.GetFieldIndex('hectare_mn')
        hectare_mn = feat.GetField(hectare_mn_id)
        pixel_count_id = feat.GetFieldIndex('num_pixels')
        pixel_count = feat.GetField(pixel_count_id)
        
        geom = feat.GetGeometryRef()
        feat_area = geom.GetArea()
        
        # Calculate water yield volume, 
        #1000 is for converting the mm of wyield to meters
        vol = wyield_mn * pixel_area * pixel_count / 1000.0
        # Get the volume field index and add value
        vol_index = feat.GetFieldIndex(vol_name)
        feat.SetField(vol_index, vol)

        # Calculate water yield volume per hectare
        vol_ha = hectare_mn * (0.0001 * feat_area)
        # Get the hectare field index and add value
        ha_index = feat.GetFieldIndex(ha_name)
        feat.SetField(ha_index, vol_ha)
        
        layer.SetFeature(feat)
        
def add_dict_to_shape(shape_uri, field_dict, field_name, key):
    """Add a new field to a shapefile with values from a dictionary.
        The dictionaries keys should match to the values of a unique fields
        values in the shapefile

        shape_uri - a URI path to a ogr datasource on disk with a unique field
            'key'. The field 'key' should have values that
            correspond to the keys of 'field_dict'

        field_dict - a python dictionary with keys mapping to values. These
            values will be what is filled in for the new field
    
        field_name - a string for the name of the new field to add
        
        key - a string for the field name in 'shape_uri' that represents
            the unique features

        returns - nothing"""

    shape = ogr.Open(shape_uri, 1)
    layer = shape.GetLayer()
    
    # Create the new field
    field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)
    layer.CreateField(field_defn)

    # Get the number of features (polygons) and iterate through each
    num_features = layer.GetFeatureCount()
    for feat_id in xrange(num_features):
        feat = layer.GetFeature(feat_id)
        
        # Get the index for the unique field
        ws_id = feat.GetFieldIndex(key)
        
        # Get the unique value that will index into the dictionary as a key
        ws_val = feat.GetField(ws_id)
        
        # Using the unique value from the field of the feature, index into the
        # dictionary to get the corresponding value
        field_val = float(field_dict[ws_val])

        # Get the new fields index and set the new value for the field
        field_index = feat.GetFieldIndex(field_name)
        feat.SetField(field_index, field_val)

        layer.SetFeature(feat)
