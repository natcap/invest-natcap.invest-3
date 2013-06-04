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

LOGGER = logging.getLogger('hydropower_core')

def water_yield(args):
    """Executes the water_yield model
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexes in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape. (required)
        
        args['soil_depth_uri'] - a uri to an input raster describing the 
            average soil depth value for each cell (mm) (required)
        
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
            'watersheds_uri' shape provided as input. (required)
        
        args['biophysical_table_uri'] - a uri to an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth (mm) and etk, which are required. 
            NOTE: these data are attributes of each LULC class rather than 
            attributes of individual cells in the raster map (required)
        
        args['seasonality_constant'] - floating point value between 1 and 10 
            corresponding to the seasonal distribution of precipitation 
            (required)
        
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
           
        returns - nothing"""
        
    LOGGER.info('Starting Water Yield Core Calculations')

    # Construct folder paths
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    service_dir = os.path.join(workspace, 'service')
    pixel_dir = os.path.join(output_dir, 'pixel')
    raster_utils.create_directories(
            [intermediate_dir, output_dir, service_dir, pixel_dir])
    
    # Get inputs from the args dictionary
    lulc_uri = args['lulc_uri']
    eto_uri = args['eto_uri']
    precip_uri = args['precipitation_uri']
    soil_depth_uri = args['soil_depth_uri']
    pawc_uri = args['pawc_uri']
    sub_sheds_uri = args['sub_watersheds_uri']
    sheds_uri = args['watersheds_uri']
    seasonality_constant = float(args['seasonality_constant'])
    
    # Open/read in the csv file into a dictionary and add to arguments
    biophysical_table_map = {}
    biophysical_table_file = open(args['biophysical_table_uri'])
    reader = csv.DictReader(biophysical_table_file)
    for row in reader:
        biophysical_table_map[int(row['lucode'])] = \
            {'etk':float(row['etk']), 'root_depth':float(row['root_depth'])}

    biophysical_table_file.close() 
    bio_dict = biophysical_table_map 
    
    # Append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
    
    # Paths for clipping the fractp/wyield raster to watershed polygons
    fractp_clipped_path = os.path.join(pixel_dir, 'fractp%s.tif' % file_suffix)
    wyield_clipped_path = os.path.join(pixel_dir, 'wyield%s.tif' % file_suffix)
    
    # Paths for the actual evapotranspiration rasters
    aet_path = os.path.join(pixel_dir, 'aet%s.tif' % file_suffix) 
    
    # Paths for the watershed and subwatershed tables
    shed_table_path = os.path.join(output_dir, 'water_yield_watershed.csv') 
    sub_table_path = os.path.join(output_dir, 'water_yield_subwatershed.csv') 
    
    # The nodata value that will be used for created output rasters
    out_nodata = float(np.finfo(np.float32).min) + 1.0
    
    # Break the bio_dict into two separate dictionaries based on
    # etk and root_depth fields to use for reclassifying 
    etk_dict = {}
    root_dict = {}
    for lulc_code in bio_dict:
        etk_dict[lulc_code] = bio_dict[lulc_code]['etk']
        root_dict[lulc_code] = bio_dict[lulc_code]['root_depth']

    # Create etk raster from table values to use in future calculations
    LOGGER.info("Reclassifying temp_etk raster")
    tmp_etk_raster_uri = raster_utils.temporary_filename()
    
    raster_utils.reclassify_dataset_uri(
            lulc_uri, etk_dict, tmp_etk_raster_uri, gdal.GDT_Float32,
            out_nodata)

    # Create root raster from table values to use in future calculations
    LOGGER.info("Reclassifying tmp_root raster")
    tmp_root_raster_uri = raster_utils.temporary_filename()
    
    raster_utils.reclassify_dataset_uri(
            lulc_uri, root_dict, tmp_root_raster_uri, gdal.GDT_Float32,
            out_nodata)

    # Get out_nodata values so that we can avoid any issues when running
    # operations
    etk_nodata = raster_utils.get_nodata_from_uri(tmp_etk_raster_uri)
    root_nodata = raster_utils.get_nodata_from_uri(tmp_root_raster_uri)
    precip_nodata = raster_utils.get_nodata_from_uri(precip_uri)
    eto_nodata = raster_utils.get_nodata_from_uri(eto_uri)
    soil_depth_nodata = raster_utils.get_nodata_from_uri(soil_depth_uri)
    pawc_nodata = raster_utils.get_nodata_from_uri(pawc_uri)
    
    # Dictionary of out_nodata values corresponding to values for fractp_op that 
    # will help avoid any out_nodata calculation issues
    fractp_nodata_dict = {'etk':etk_nodata, 
                          'root':root_nodata,
                          'precip':precip_nodata,
                          'eto':eto_nodata,
                          'soil':soil_depth_nodata,
                          'pawc':pawc_nodata}
    
    def fractp_op(etk, eto, precip, root, soil, pawc):
        """A wrapper function to call hydropower's cython core. Acts as a
            closure for fractp_nodata_dict, out_nodata, seasonality_constant
            """

        return hydropower_cython_core.fractp_op(
            fractp_nodata_dict, out_nodata, seasonality_constant, etk,
            eto, precip, root, soil, pawc)
    
    # Vectorize operation
    fractp_vec = np.vectorize(fractp_op)
    
    # Get pixel size from tmp_etk_raster_uri which should be the same resolution
    # as LULC raster
    pixel_size = raster_utils.get_cell_size_from_uri(tmp_etk_raster_uri)

    raster_list = [
            tmp_etk_raster_uri, eto_uri, precip_uri, tmp_root_raster_uri,
            soil_depth_uri, pawc_uri]
    
    # Create clipped fractp_clipped raster
    raster_utils.vectorize_datasets(
            raster_list, fractp_vec, fractp_clipped_path, gdal.GDT_Float32,
            out_nodata, pixel_size, 'intersection', aoi_uri=sub_sheds_uri)
    
    LOGGER.debug('Performing wyield operation')
    
    def wyield_op(fractp, precip):
        """Function that calculates the water yeild raster
        
           fractp - numpy array with the fractp raster values
           precip - numpy array with the precipitation raster values (mm)
           
           returns - water yield value (mm)"""
        
        if fractp == out_nodata or precip == precip_nodata:
            return out_nodata
        else:
            return (1.0 - fractp) * precip
    
    # Create clipped wyield_clipped raster
    raster_utils.vectorize_datasets(
            [fractp_clipped_path, precip_uri], wyield_op, wyield_clipped_path,
            gdal.GDT_Float32, out_nodata, pixel_size, 'intersection',
            aoi_uri=sub_sheds_uri)

    # Making a copy of watershed and sub-watershed to add output results to
    sub_sheds_out_uri = os.path.join(output_dir, 'sub_sheds.shp')
    sheds_out_uri = os.path.join(output_dir, 'sheds.shp')
    raster_utils.copy_datasource_uri(sub_sheds_uri, sub_sheds_out_uri)
    raster_utils.copy_datasource_uri(sheds_uri, sheds_out_uri)

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
            aoi_uri=sub_sheds_uri)
   
    # Create a list of tuples that pair up field names and raster uris so that
    # we can nicely do operations below
    sws_tuple_names_uris = [
            ('precip_mn', precip_uri),('PET_mn', eto_uri),
            ('AET_mn', aet_path),('wyield_mn', wyield_clipped_path),
            ('fractp_mn', fractp_clipped_path)]
   
    for key_name, rast_uri in sws_tuple_names_uris:
        # Aggregrate mean over the sub-watersheds for each uri listed in
        # 'sws_tuple_names_uri'
        key_dict = raster_utils.aggregate_raster_values_uri(
                rast_uri, sub_sheds_uri, 'subws_id', 'mean')
        # Add aggregated values to sub-watershed shapefile under new field
        # 'key_name'
        add_dict_to_shape(sub_sheds_out_uri, key_dict, key_name, 'subws_id')
  
    # Aggregate the water yield by summing pixels over sub-watersheds
    wyield_sum_dict = raster_utils.aggregate_raster_values_uri(
            wyield_clipped_path, sub_sheds_uri, 'subws_id', 'sum')
    
    # Add aggregated water yield sums to sub-watershed shapefile
    add_dict_to_shape(
            sub_sheds_out_uri, wyield_sum_dict, 'wyield_sum', 'subws_id')
    
    # Compute the water yield volume and water yield volume per hectare. The
    # values per sub-watershed will be added as fields in the sub-watersheds
    # shapefile
    compute_water_yield_volume(sub_sheds_out_uri)
    
    # Create a dictionary that maps watersheds to sub-watersheds given the
    # watershed and sub-watershed shapefiles
    wsr = sheds_map_subsheds(sheds_uri, sub_sheds_uri)
    LOGGER.debug('wsr : %s', wsr)
    
    # Create a dictionary that maps sub-watersheds to watersheds
    sws_dict = {}
    for key, val in wsr.iteritems():
        sws_dict[key] = val
    
    LOGGER.debug('sws_dict : %s', sws_dict)
   
    # Add the corresponding watershed ids to the sub-watershed shapefile as a
    # new field
    add_dict_to_shape(sub_sheds_out_uri, sws_dict, 'ws_id', 'subws_id')
    
    # List of wanted fields to output in the sub-watershed CSV table
    sub_field_list = [
            'ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
            'wyield_mn', 'wyield_sum']
    
    # Get a dictionary from the sub-watershed shapefiles attributes based on the
    # fields to be outputted to the CSV table
    sub_value_dict = extract_datasource_table_by_key(
            sub_sheds_out_uri, 'subws_id', sub_field_list)
    
    LOGGER.debug('sub_value_dict : %s', sub_value_dict)
    
    # Write sub-watershed CSV table
    write_new_table(sub_table_path, sub_field_list, sub_value_dict)
    
    # Create a list of tuples that pair up field names and raster uris so that
    # we can nicely do operations below
    ws_tuple_names_uris = [
            ('precip_mn', precip_uri),('PET_mn', eto_uri),
            ('AET_mn', aet_path),('wyield_mn', wyield_clipped_path)]
   
    for key_name, rast_uri in ws_tuple_names_uris:
        # Aggregrate mean over the watersheds for each uri listed in
        # 'ws_tuple_names_uri'
        key_dict = raster_utils.aggregate_raster_values_uri(
                rast_uri, sheds_uri, 'ws_id', 'mean')
        # Add aggregated values to watershed shapefile under new field
        # 'key_name'
        add_dict_to_shape(sheds_out_uri, key_dict, key_name, 'ws_id')

    # Aggregate the water yield by summing pixels over the watersheds
    wyield_sum_dict = raster_utils.aggregate_raster_values_uri(
            wyield_clipped_path, sheds_uri, 'ws_id', 'sum')
        
    # Add aggregated water yield sums to watershed shapefile
    add_dict_to_shape(sheds_out_uri, wyield_sum_dict, 'wyield_sum', 'ws_id')
    
    # List of wanted fields to output in the watershed CSV table
    field_list = [
            'ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 'wyield_sum']
    
    # Get a dictionary from the watershed shapefiles attributes based on the
    # fields to be outputted to the CSV table
    value_dict = extract_datasource_table_by_key(
            sheds_out_uri, 'ws_id', field_list)
    
    LOGGER.debug('value_dict : %s', value_dict)
    
    # Write watershed CSV table
    write_new_table(shed_table_path, field_list, value_dict)

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

def compute_water_yield_volume(shape_uri):
    """Calculate the water yield volume per sub-watershed and the water yield
        volume per hectare per sub-watershed. Add results to shape_uri, units
        are cubic meters

        shape_uri - a URI path to an ogr datasource for the sub-watershed
            shapefile. This shapefiles features should have a 'wyield_mn'
            attribute, which calculations are derived from

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
        
        geom = feat.GetGeometryRef()
        feat_area = geom.GetArea()
        
        # Calculate water yield volume
        vol = wyield_mn * feat_area / 1000.0
        # Get the volume field index and add value
        vol_index = feat.GetFieldIndex(vol_name)
        feat.SetField(vol_index, vol)

        # Calculate water yield volume per hectare
        vol_ha = vol / (0.0001 * feat_area)
        # Get the hectare field index and add value
        ha_index = feat.GetFieldIndex(ha_name)
        feat.SetField(ha_index, vol_ha)
        
        layer.SetFeature(feat)
        
def add_dict_to_shape(shape_uri, field_dict, field_name, shed_name):
    """Add a new field to a shapefile with values from a dictionary.
        The dictionaries keys should match to the values of a unique fields
        values in the shapefile

        shape_uri - a URI path to a ogr datasource on disk with a unique field
            'shed_name'. The field 'shed_name' should have values that
            correspond to the keys of 'field_dict'

        field_dict - a python dictionary with keys mapping to values. These
            values will be what is filled in for the new field 
    
        field_name - a string for the name of the new field to add
        
        shed_name - a string for the field name in 'shape_uri' that represents
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
        ws_id = feat.GetFieldIndex(shed_name)
        
        # Get the unique value that will index into the dictionary as a key
        ws_val = feat.GetField(ws_id)
        
        # Using the unique value from the field of the feature, index into the
        # dictionary to get the corresponding value
        field_val = float(field_dict[ws_val])

        # Get the new fields index and set the new value for the field
        field_index = feat.GetFieldIndex(field_name)
        feat.SetField(field_index, field_val)

        layer.SetFeature(feat)

def sheds_map_subsheds(shape_uri, sub_shape_uri):
    """Stores which sub watersheds belong to which watershed
       
       shape - an OGR shapefile of the watersheds
       sub_shape - an OGR shapefile of the sub watersheds
       
       returns - a dictionary where the keys are the sub watersheds id's
                 and whose value is the watersheds id it belongs to
    """
    
    LOGGER.debug('Starting sheds_map_subsheds')
    shape = ogr.Open(shape_uri)
    sub_shape = ogr.Open(sub_shape_uri)
    layer = shape.GetLayer(0)
    sub_layer = sub_shape.GetLayer(0)
    collection = {}
    # For all the polygons in the watershed check to see if any of the polygons
    # in the sub watershed belong to that watershed by checking the area of the
    # watershed against the area of the Union of the watershed and sub watershed
    # polygon.  The areas will be the same if the sub watershed is part of the
    # watershed and will be different if it is not
    for feat in layer:
        index = feat.GetFieldIndex('ws_id')
        ws_id = feat.GetFieldAsInteger(index)
        geom = feat.GetGeometryRef()
        sub_layer.ResetReading()
        for sub_feat in sub_layer:
            sub_index = sub_feat.GetFieldIndex('subws_id')
            sub_id = sub_feat.GetFieldAsInteger(sub_index)
            sub_geom = sub_feat.GetGeometryRef()
            u_geom = sub_geom.Union(geom)
            # We can't be sure that the areas will be identical because of
            # floating point issues and complete accuracy so we make sure the
            # difference in areas is within reason
            # It also could be the case that the polygons were intended to 
            # overlap but do not overlap exactly
            if abs(geom.GetArea() - u_geom.GetArea()) < (math.e**-5):
                collection[sub_id] = ws_id
            
            sub_feat.Destroy()
            
        feat.Destroy()
        
    return collection

def water_scarcity(args):
    """Executes the water scarcity model
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc'] - a GDAL raster dataset of land use/land cover whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['watersheds'] - a OGR shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds'] - a OGR shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds' shape provided as input. (required)
        args['watershed_yield_table'] - a dictionary, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per watershed
        args['subwatershed_yield_table'] - a dictionary, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per sub watershed
        args['demand_table'] - a dictionary of LULC classes,
            showing consumptive water use for each landuse / land-cover type
            (required)
        args['hydro_calibration_table'] - a dictionary of 
            hydropower stations with associated calibration values (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional) 
        
        returns nothing"""

    LOGGER.info('Starting Water Scarcity Core Calculations')
    
    # Construct folder paths
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    service_dir = os.path.join(workspace, 'service')
    raster_utils.create_directories(
            [intermediate_dir, output_dir, service_dir])
    
    # Append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
    
    # Get arguments
    demand_dict = args['demand_table']
    lulc_raster = args['lulc']
    calib_dict = args['hydro_calibration_table']
    wyield_vol_raster = args['water_yield_vol']
    watersheds = args['watersheds']
    sub_sheds = args['sub_watersheds']
    water_shed_table = args['watershed_yield_table']
    sub_shed_table = args['subwatershed_yield_table']
    wyield_mean = args['water_yield_mn']
        
    # Path for the calibrated water yield volume per sub-watershed
    wyield_calib_path = os.path.join(output_dir, 'cyield_vol') 
    # Path for mean and total water consumptive volume
    consump_vol_path = os.path.join(output_dir, 'consum_vol') 
    consump_mean_path = os.path.join(output_dir, 'consum_mn') 
    clipped_consump_path = os.path.join(intermediate_dir, 'clipped_consump') 
    # Paths for realized and mean realized water supply volume
    rsupply_vol_path = os.path.join(output_dir, 'rsup_vol') 
    rsupply_mean_path = os.path.join(output_dir, 'rsup_mn') 
    # Paths for watershed and sub watershed scarcity tables
    ws_out_table_name = os.path.join(output_dir, 'water_scarcity_watershed') 
    sws_out_table_name = os.path.join(output_dir, 'water_scarcity_subwatershed') 
    
    #Open/read in the csv files into a dictionary and add to arguments
    watershed_yield_table_map = {}
    watershed_yield_table_file = open(args['watershed_yield_table_uri'])
    reader = csv.DictReader(watershed_yield_table_file)
    for row in reader:
        watershed_yield_table_map[int(row['ws_id'])] = row
    
    watershed_yield_table_file.close()
    
    subwatershed_yield_table_map = {}
    subwatershed_yield_table_file = open(args['subwatershed_yield_table_uri'])
    reader = csv.DictReader(subwatershed_yield_table_file)
    for row in reader:
        subwatershed_yield_table_map[int(row['subws_id'])] = row
    
    subwatershed_yield_table_file.close()
    
    demand_table_map = {}
    demand_table_file = open(args['demand_table_uri'])
    reader = csv.DictReader(demand_table_file)
    for row in reader:
        demand_table_map[int(row['lucode'])] = int(row['demand'])
    
    LOGGER.debug('Demand_Dict : %s', demand_table_map)
    demand_table_file.close()
    
    hydro_cal_table_map = {}
    hydro_cal_table_file = open(args['hydro_calibration_table_uri'])
    reader = csv.DictReader(hydro_cal_table_file)
    for row in reader:
        hydro_cal_table_map[int(row['ws_id'])] = float(row['calib'])
        
    hydro_cal_table_file.close()
    
    # The nodata value to use for the output rasters
    out_nodata = float(np.finfo(np.float32).min) + 1.0
    
    # Create watershed mask raster
    ws_mask_uri = raster_utils.temporary_filename()
    ws_mask = raster_utils.new_raster_from_base(
        wyield_vol_raster, ws_mask_uri, 'GTiff', out_nodata,
        gdal.GDT_Int32)

    gdal.RasterizeLayer(ws_mask, [1], watersheds.GetLayer(0),
                        options = ['ATTRIBUTE=ws_id'])
    
    calib_raster_uri = raster_utils.temporary_filename()
    raster_utils.reclassify_dataset(
        ws_mask, calib_dict, calib_raster_uri, gdal.GDT_Float32, out_nodata)
    calib_raster = gdal.Open(calib_raster_uri)

    wyield_vol_nodata = wyield_vol_raster.GetRasterBand(1).GetNoDataValue()
    
    def cyield_vol_op(wyield_vol, calib_val):
        """Function that computes the calibrated water yield volume
           per sub-watershed
        
           wyield_vol - a numpy array of water yield volume values
           calib_val - a numpy array of calibrated values
                                
           returns - the calibrated water yield volume value (cubic meters)
        """
        
        if wyield_vol != wyield_vol_nodata and calib_val != out_nodata:
            return wyield_vol * calib_val
        else:
            return out_nodata
        
    LOGGER.info('Creating cyield raster')
    # Multiply calibration with wyield_vol raster to get cyield_vol
    wyield_calib = \
        raster_utils.vectorize_rasters([wyield_vol_raster, calib_raster], 
                                       cyield_vol_op, aoi=watersheds, 
                                       raster_out_uri = wyield_calib_path, 
                                       nodata=out_nodata)
    
    # Create raster from land use raster, subsituting in demand value
    clipped_consump_raster_uri = raster_utils.temporary_filename()
    raster_utils.reclassify_dataset(
        lulc_raster, demand_dict, clipped_consump_raster_uri,
        gdal.GDT_Float32, out_nodata)
    clipped_consump = gdal.Open(clipped_consump_raster_uri)


    LOGGER.info('Creating consump_vol raster')
    
    sum_dict = \
        raster_utils.aggregate_raster_values(clipped_consump, sub_sheds,
                'subws_id', 'sum', aggregate_uri = consump_vol_path, 
                 intermediate_directory = intermediate_dir)
    
    sum_raster = gdal.Open(consump_vol_path) 
        
    LOGGER.debug('sum_dict : %s', sum_dict)
    
    # Take mean of consump over sub watersheds making conusmp_mean
    LOGGER.info('Creating consump_mn raster')
    mean_dict = \
        raster_utils.aggregate_raster_values(clipped_consump, sub_sheds,
                'subws_id', 'mean', aggregate_uri = consump_mean_path, 
                 intermediate_directory = intermediate_dir, 
                 ignore_nodata = False)
    
    mean_raster = gdal.Open(consump_mean_path)
    LOGGER.debug('mean_dict : %s', mean_dict)

    nodata_calib = wyield_calib.GetRasterBand(1).GetNoDataValue()
    nodata_consump = sum_raster.GetRasterBand(1).GetNoDataValue()
    
    rsupply_out_nodata = 0.0
    
    def rsupply_vol_op(wyield_calib, consump_vol):
        """Function that computes the realized water supply volume
        
           wyield_calib - a numpy array with the calibrated water yield values
                          (cubic meters)
           consump_vol - a numpy array with the total water consumptive use
                         values (cubic meters)
           
           returns - the realized water supply volume value (cubic meters)
        """
        if wyield_calib != nodata_calib and consump_vol != nodata_consump:
            return wyield_calib - consump_vol
        else:
            return rsupply_out_nodata
        
    rsupply_vol_vec = np.vectorize(rsupply_vol_op)
    LOGGER.info('Creating rsupply_vol raster')
    # Make rsupply_vol by wyield_calib minus consump_vol
    raster_utils.vectorize_rasters([wyield_calib, sum_raster], rsupply_vol_vec, 
                                   raster_out_uri=rsupply_vol_path, 
                                   nodata=rsupply_out_nodata)
    
    wyield_mn_nodata = wyield_mean.GetRasterBand(1).GetNoDataValue()
    mn_raster_nodata = mean_raster.GetRasterBand(1).GetNoDataValue()
    
    rsupply_mean_out_nodata = 0.0
   
    def rsupply_mean_op(wyield_mean, consump_mean):
        """Function that computes the mean realized water supply
        
           wyield_mean - a numpy array with the mean calibrated water yield 
                         values (mm)
           consump_mean - a numpy array with the mean water consumptive use
                         values (cubic meters)
           
           returns - the mean realized water supply value
        """
        # THIS MAY BE WRONG. DOING OPERATION ON (mm) and (cubic m)#
        if wyield_mean != wyield_mn_nodata and consump_mean != mn_raster_nodata:
            return wyield_mean - consump_mean
        else:
            return rsupply_mean_out_nodata
        
    rsupply_mn_vec = np.vectorize(rsupply_mean_op)
    LOGGER.info('Creating rsupply_mn raster')
    raster_utils.vectorize_rasters([wyield_mean, mean_raster], rsupply_mn_vec, 
                                   raster_out_uri=rsupply_mean_path,
                                   nodata=rsupply_mean_out_nodata)
    
    # Make sub watershed and watershed tables by adding values onto the tables
    # provided from sub watershed yield and watershed yield
    
    # cyielc_vl per watershed
    shed_subshed_map = {}
    for key, val in sub_shed_table.iteritems():
        if int(val['ws_id']) in shed_subshed_map:
            shed_subshed_map[int(val['ws_id'])].append(key)
        else:
            shed_subshed_map[int(val['ws_id'])] = [key]
            
    LOGGER.debug('shed_subshed_map : %s', shed_subshed_map) 
    
    new_keys_ws = {}
    new_keys_sws = {}
    
    field_name = 'ws_id'
    cyield_d = \
        raster_utils.aggregate_raster_values(wyield_calib, sub_sheds,\
                                             'subws_id', 'mean')
    
    cyield_vol_d = sum_mean_dict(shed_subshed_map, cyield_d, 'sum')
    new_keys_ws['cyield_vl'] = cyield_vol_d
    new_keys_sws['cyield_vl'] = cyield_d
    
    # consump_vl per watershed
    consump_vl_d = sum_mean_dict(shed_subshed_map, sum_dict, 'sum')
    new_keys_ws['consump_vl'] = consump_vl_d
    new_keys_sws['consump_vl'] = sum_dict
    
    # consump_mean per watershed
    consump_mn_d = sum_mean_dict(shed_subshed_map, mean_dict, 'mean')
    new_keys_ws['consump_mn'] = consump_mn_d
    new_keys_sws['consump_mn'] = mean_dict
    
    # rsupply_vl per watershed
    rsupply_vl_raster = gdal.Open(rsupply_vol_path)
    field_name = 'ws_id'
    rsupply_vl_d = {} 
    rsupply_mn_d = {} 
    for key in cyield_d:
        rsupply_vl_d[key] = cyield_d[key] - sum_dict[key]
        rsupply_mn_d[key] = float(sub_shed_table[key]['wyield_mn']) - mean_dict[key]
    LOGGER.debug('rsupply_vl_d : %s', rsupply_vl_d) 
    rsupply_vl_dt = sum_mean_dict(shed_subshed_map, rsupply_vl_d, 'sum')
    new_keys_ws['rsupply_vl'] = rsupply_vl_dt
    new_keys_sws['rsupply_vl'] = rsupply_vl_d
    
    # rsupply_mn per watershed
    rsupply_mn_raster = gdal.Open(rsupply_mean_path)
    field_name = 'ws_id'
    
    rsupply_mn_dt = sum_mean_dict(shed_subshed_map, rsupply_mn_d, 'mean')
    new_keys_ws['rsupply_mn'] = rsupply_mn_dt
    new_keys_sws['rsupply_mn'] = rsupply_mn_d
    
    field_list_ws = ['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 
                     'wyield_sum', 'cyield_vl', 'consump_vl', 'consump_mn',
                     'rsupply_vl', 'rsupply_mn']
    
    field_list_sws = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
                      'wyield_mn', 'wyield_sum', 'cyield_vl', 'consump_vl', 
                      'consump_mn','rsupply_vl', 'rsupply_mn']
    
    for key, val in water_shed_table.iteritems():
        for index, item in new_keys_ws.iteritems():
            val[index] = item[key]
    
    for key, val in sub_shed_table.iteritems():
        for index, item in new_keys_sws.iteritems():
            val[index] = item[key]
    
    LOGGER.info('Creating CSV Files')
    write_csv_table(water_shed_table, field_list_ws, ws_out_table_name)
    write_csv_table(sub_shed_table, field_list_sws, sws_out_table_name)
    
def write_csv_table(shed_table, field_list, file_path):
    """Creates a CSV table and writes it to disk
    
       shed_table - a dictionary where each key points to another dictionary 
                    which is a row of the csv table
       field_list - a python list of Strings that contain the ordered fields
                    for the csv file output
       file_path - a String uri that is the destination of the csv file
       
       returns - Nothing
    """
    shed_file = open(file_path, 'wb')
    writer = csv.DictWriter(shed_file, field_list)
    field_dict = {}
    # Create a dictionary with field names as keys and the same field name
    # as values, to use as first row in CSV file which will be the column header
    for field in field_list:
        field_dict[field] = field
    # Write column header row
    writer.writerow(field_dict)
    
    for sub_dict in shed_table.itervalues():
        writer.writerow(sub_dict)
    
    shed_file.close()

def sum_mean_dict(dict1, dict2, op_val):
    """Creates a dictionary by calculating the mean or sum of values over
       sub watersheds for the watershed
    
       dict1 - a dictionary whose keys are the watershed id's, which point to
               a python list whose values are the sub wateshed id's that fall
               within that watershed
       dict2 - a dictionary whose keys are sub watershed id's and
               whose values are the desired numbers to be summed or meaned
       op_val - a string indicating which operation to do ('sum' or 'mean')
       
       returns - a dictionary
    """
    new_dict = {}
    for key, val in dict1.iteritems():
        sum_ws = 0
        counter = 0
        for item in val:
            counter = counter + 1
            sum_ws = sum_ws + dict2[int(item)]
        if op_val == 'sum':
            new_dict[key] = sum_ws
        if op_val == 'mean':
            new_dict[key] = sum_ws / counter
    
    LOGGER.debug('sum_ws_dict rsupply_mean: %s', new_dict)
    return new_dict

def valuation(args):
    """This function invokes the valuation model for hydropower
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['cyield_vol'] - a Gdal raster of the calibrated
            water yield volume per sub-watershed, generated as an output
            of the water scarcity model (cubic meters) (required)
        args['consump_vol'] - a Gdal raster of the total water
            consumptive use for each sub-watershed, generated as an output
            of the water scarcity model (cubic meters) (required)
        args['watersheds'] - a OGR shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds'] - a OGR shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['watershed_scarcity_table'] - a dictionary, that holds
            relevant values for each watershed. (required)
        args['subwatershed_scarcity_table'] - a dictionary, that holds
            relevant values for each sub watershed. (required)
        args['valuation_table'] - a dictionary containing values of the 
            hydropower stations with the keys being watershed id and
            the values be a dictionary representing valuation information 
            corresponding to that id with the following structure (required):
            
                valuation_table[1] = {'ws_id':1, 'time_span':100, 'discount':5,
                                      'efficiency':0.75, 'fraction':0.6, 'cost':0,
                                      'height':25, 'kw_price':0.07}
            
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional) 
           
        returns - nothing"""
        
    # water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')
    
    # Construct folder paths
    workspace_dir = args['workspace_dir']
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'
    
    # Get arguments
    watersheds = args['watersheds']
    sub_sheds = args['sub_watersheds']
    ws_scarcity_table = args['watershed_scarcity_table']
    sws_scarcity_table = args['subwatershed_scarcity_table']
    valuation_table = args['valuation_table']
    cyield_vol = args['cyield_vol']
    water_consump = args['consump_vol']
    
    # Suffix handling
    suffix = args['results_suffix']
    if len(suffix) > 0:
        suffix_tif = '_' + suffix + '.tif'
        suffix_csv = '_' + suffix + '.csv'
    else:
        suffix_tif = '.tif'
        suffix_csv = '.csv'
    
    # Paths for the watershed and subwatershed tables
    watershed_value_table = \
        service_dir + os.sep + 'hydropower_value_watershed' + suffix_csv
    subwatershed_value_table = \
        service_dir + os.sep + 'hydropower_value_subwatershed' + suffix_csv
    # Paths for the hydropower value and energy rasters
    hp_val_path = service_dir + os.sep + 'hp_val' + suffix_tif
    hp_energy_path = service_dir + os.sep + 'hp_energy' + suffix_tif
    
    energy_dict = {}
    npv_dict = {}
    # For each watershed compute the energy production and npv
    for key in ws_scarcity_table.keys():
        val_row = valuation_table[key]
        ws_row = ws_scarcity_table[key]
        efficiency = float(val_row['efficiency'])
        fraction = float(val_row['fraction'])
        height = float(val_row['height'])
        rsupply_vl = float(ws_row['rsupply_vl'])
        
        # Compute hydropower energy production (KWH)
        # Not confident about units here and the constant 0.00272 is 
        # for conversion??
        energy = efficiency * fraction * height * rsupply_vl * 0.00272
        energy_dict[key] = energy
        
        time = int(val_row['time_span'])
        kwval = float(val_row['kw_price'])
        disc = float(val_row['discount'])
        cost = float(val_row['cost'])
        
        dsum = 0
        # Divide by 100 because it is input at a percent and we need
        # decimal value
        disc = disc / 100
        # To calculate the summation of the discount rate term over the life 
        # span of the dam we can use a geometric series
        ratio = 1 / (1+disc)
        dsum = (1 - math.pow(ratio, time)) / (1 - ratio)
        
        npv = ((kwval * energy) - cost) * dsum
        npv_dict[key] = npv
        ws_scarcity_table[key]['hp_value'] = npv
        ws_scarcity_table[key]['hp_energy'] = energy

    # npv for sub shed is npv for water shed times ratio of rsupply_vl of 
    # sub shed to rsupply_vl of water shed
    sws_npv_dict = {}
    sws_energy_dict = {}
    
    for key, val in sws_scarcity_table.iteritems():
        ws_id = int(val['ws_id'])
        subws_rsupply_vl = float(val['rsupply_vl'])
        ws_rsupply_vl = float(ws_scarcity_table[ws_id]['rsupply_vl'])
        
        npv = npv_dict[ws_id] * (subws_rsupply_vl / ws_rsupply_vl)
        energy = energy_dict[ws_id] * (subws_rsupply_vl / ws_rsupply_vl)
        
        sws_npv_dict[key] = npv
        sws_energy_dict[key] = energy
        
        sws_scarcity_table[key]['hp_value'] = npv
        sws_scarcity_table[key]['hp_energy'] = energy
    
    LOGGER.debug('sub energy dict : %s', sws_energy_dict)
    LOGGER.debug('sub npv dict : %s', sws_npv_dict)
    
    field_list_ws = ['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 
                     'wyield_sum', 'cyield_vl', 'consump_vl', 'consump_mn',
                     'rsupply_vl', 'rsupply_mn', 'hp_energy', 'hp_value']
    
    field_list_sws = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
                      'wyield_mn', 'wyield_sum', 'cyield_vl', 'consump_vl', 
                      'consump_mn','rsupply_vl', 'rsupply_mn', 'hp_energy', 
                      'hp_value']
    
    write_csv_table(ws_scarcity_table, field_list_ws, \
                         watershed_value_table)
    write_csv_table(sws_scarcity_table, field_list_sws, \
                         subwatershed_value_table)
    out_nodata = -1.0

    hp_val_watershed_mask_uri = raster_utils.temporary_filename()
    hp_val_watershed_mask = raster_utils.new_raster_from_base(
        water_consump, hp_val_watershed_mask_uri, 'GTiff', out_nodata,
        gdal.GDT_Int32)

    gdal.RasterizeLayer(hp_val_watershed_mask, [1], sub_sheds.GetLayer(0),
                        options = ['ATTRIBUTE=subws_id'])
    
    # create hydropower value raster
    LOGGER.debug('Create Hydropower Value Raster')
    raster_utils.reclassify_dataset(
        hp_val_watershed_mask, sws_npv_dict, hp_val_path, gdal.GDT_Float32, out_nodata)

    hp_energy_watershed_mask_uri = raster_utils.temporary_filename()
    hp_energy_watershed_mask = raster_utils.new_raster_from_base(
        water_consump, hp_energy_watershed_mask_uri, 'GTiff', out_nodata,
        gdal.GDT_Int32)
   
    gdal.RasterizeLayer(hp_energy_watershed_mask, [1], sub_sheds.GetLayer(0),
                        options = ['ATTRIBUTE=subws_id'])
    
    # create hydropower energy raster
    LOGGER.debug('Create Hydropower Energy Raster')
    raster_utils.reclassify_dataset(
        hp_energy_watershed_mask, sws_energy_dict, hp_energy_path, gdal.GDT_Float32, out_nodata)
