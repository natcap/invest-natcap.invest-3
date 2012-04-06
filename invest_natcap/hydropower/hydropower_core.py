"""Module that contains the core computational components for the hydropower
    model including the water yield, water scarcity , and valuation functions"""

import logging
import os
import csv
import math

import numpy as np
from osgeo import gdal
from osgeo import ogr

import invest_cython_core
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('hydropower_core')

def water_yield(args):
    """Executes the water_yield model
    
        args - is a dictionary with at least the following entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc'] - a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['soil_depth'] - an input raster describing the 
            average soil depth value for each cell (mm) (required)
        args['precipitation'] - an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        args['pawc'] - an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        args['eto'] - an input raster describing the 
            annual average evapotranspiration value for each cell. Potential
            evapotranspiration is the potential loss of water from soil by
            both evaporation from the soil and transpiration by healthy Alfalfa
            (or grass) if sufficient water is available (mm) (required)
        args['watersheds'] - an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds'] - an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['biophysical_dictionary'] - an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth and etk. NOTE: these data are 
            attributes of each LULC class rather than attributes of individual 
            cells in the raster map (required)
        args['seasonality_constant'] - floating point value between 1 and 10 corresponding
            to the seasonal distribution of precipitation (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)    
           
        returns nothing"""
        
    LOGGER.info('Starting Water Yield Core Calculations')

    #Construct folder paths
    workspace_dir = args['workspace_dir']
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'

    #Get inputs from the args dictionary
    suffix = args['results_suffix']
    bio_dict = args['biophysical_dictionary']
    lulc_raster = args['lulc']
    eto_raster = args['ape']
    precip_raster = args['precipitation']
    soil_depth_raster = args['soil_depth']
    pawc_raster = args['pawc']
    sub_sheds = args['sub_watersheds']
    sheds = args['watersheds']
    seasonality_constant = float(args['seasonality_constant'])
    
    #Collection of output and temporary path names
    if len(suffix) > 0:
        suffix_tif = '_' + suffix + '.tif'
        suffix_csv = '_' + suffix + '.csv'
    else:
        suffix_tif = '.tif'
        suffix_csv = '.csv'
    
    #Paths for the etk and root_depth rasters from the biophysical table
    tmp_etk_path = intermediate_dir + os.sep + 'tmp_etk' + suffix_tif
    tmp_root_path = intermediate_dir + os.sep + 'tmp_root' + suffix_tif
    
    #Paths for the actual evapotranspiration fraction of precipitation raster
    #and water yield raster
    fractp_path = intermediate_dir + os.sep + 'fractp' + suffix_tif
    wyield_path = intermediate_dir + os.sep + 'wyield' + suffix_tif
    
    #Paths for clipping the fractp/wyield raster to watershed polygons
    fractp_clipped_path = \
        intermediate_dir + os.sep + 'fractp_clipped' + suffix_tif
    wyield_clipped_path = \
        intermediate_dir + os.sep + 'wyield_clipped' + suffix_tif
    
    #Paths for the fractp mean and water yield mean, area, and volume rasters
    fractp_mean_path = output_dir + os.sep + 'fractp_mn' + suffix_tif
    wyield_mean_path = service_dir + os.sep + 'wyield_mn' + suffix_tif
    wyield_area_path = intermediate_dir + os.sep + 'wyield_area' + suffix_tif
    wyield_volume_path = \
        service_dir + os.sep + 'wyield_volume' + suffix_tif
    wyield_ha_path = service_dir + os.sep + 'wyield_ha' + suffix_tif
    
    #Paths for the actual evapotranspiration rasters
    aet_path = intermediate_dir + os.sep + 'aet' + suffix_tif
    aet_mean_path = output_dir + os.sep + 'aet_mn' + suffix_tif
    
    #Paths for the watershed and subwatershed mask rasters
    sub_mask_raster_path = \
        intermediate_dir + os.sep + 'sub_shed_mask' + suffix_tif
    shed_mask_raster_path = \
        intermediate_dir + os.sep + 'shed_mask' + suffix_tif
    
    #Paths for the watershed and subwatershed tables
    shed_table_path = \
        output_dir + os.sep + 'water_yield_watershed' + suffix_csv
    sub_table_path = \
        output_dir + os.sep + 'water_yield_subwatershed' + suffix_csv
    
    #The nodata value that will be used for created output rasters
    nodata = -1
    
    #Create etk raster from table values to use in future calculations
    tmp_etk_raster = \
        raster_from_table_values(lulc_raster, tmp_etk_path, bio_dict, 'etk')
    
    #Create root raster from table values to use in future calculations
    tmp_root_raster = raster_from_table_values(lulc_raster, tmp_root_path, 
                                               bio_dict, 'root_depth')
    
    def fractp(etk, eto, precip, root, soil, pawc):
        """Function that calculates the fractp (actual evapotranspiration
           fraction of precipitation) raster
        
            etk - numpy array with the etk (plant evapotranspiration 
                  coefficient) raster values
            eto - numpy array with the potential evapotranspiration raster 
                  values
            precip - numpy array with the precipitation raster values
            root - numpy array with the root depth (maximum root depth for
                   vegetated land use classes) raster values
            soil - numpy array with the soil depth raster values
            pawc - numpy array with the plant available water content raster 
                   values
            
        returns - fractp value"""
        
        tmp_pet = (etk * eto) / 1000
        tmp_DI = tmp_pet / precip        
        awc = (np.minimum(root, soil) * pawc)        
        tmp_w = (awc / (precip + 1)) * seasonality_constant
        
        tmp_max_aet = np.copy(tmp_DI)
        
        #Replace any value greater than 1 with 1
        np.putmask(tmp_max_aet, tmp_max_aet > 1, 1)
        
        tmp_calc = \
            ((tmp_w * tmp_DI + 1) / (( 1 / tmp_DI) + (tmp_w * tmp_DI + 1)))
        
        fractp = np.minimum(tmp_max_aet, tmp_calc)
        
        return fractp
    
    #Create the fractp raster
    raster_list = [tmp_etk_raster, eto_raster, precip_raster, tmp_root_raster,
                   soil_depth_raster, pawc_raster]
    fractp_raster = invest_core.vectorizeRasters(raster_list, fractp, 
                                                 rasterName=fractp_path)
    
    def wyield(fractp, precip):
        """Function that calculates the water yeild raster
        
           fractp - numpy array with the fractp raster values
           precip - numpy array with the precipitation raster values
           
           returns - water yield value"""
           
        return (1 - fractp) * precip
    
    #Create the water yield raster 
    wyield_raster = \
        invest_cython_core.newRasterFromBase(fractp_raster, wyield_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
        
    #Get relevant raster bands for creating water yield raster
    fractp_band = fractp_raster.GetRasterBand(1)
    precip_band = precip_raster.GetRasterBand(1)
    wyield_band = wyield_raster.GetRasterBand(1)
    
    invest_core.vectorize2ArgOp(fractp_band, precip_band, wyield, wyield_band)
    
    #Clip fractp/wyield rasters to watershed polygons
    wyield_clipped_raster = clip_raster_from_polygon(sheds, wyield_raster, \
                                                     wyield_clipped_path)
    fractp_clipped_raster = clip_raster_from_polygon(sheds, fractp_raster, \
                                                     fractp_clipped_path)
    
    #Get a numpy array from rasterizing the sub watershed id values into
    #a raster. The numpy array will be the sub watershed mask used for
    #calculating mean and sum values at a sub watershed basis
    sub_mask = get_mask(fractp_clipped_raster, sub_mask_raster_path, sub_sheds, 
                        'subws_id')
    sws_id_list = get_shed_ids(sub_mask, nodata)
    
    #Get a numpy array from rasterizing the watershed id values into
    #a raster. The numpy array will be the watershed mask used for
    #calculating mean and sum values at a per watershed basis
    shed_mask = get_mask(fractp_clipped_raster, shed_mask_raster_path,
                               sheds, 'ws_id')
    ws_id_list = get_shed_ids(shed_mask, nodata)
    
    #Create mean rasters for fractp and water yield
    fract_mn_dict = {}
    wyield_mn_dict = {}
    fractp_mean = create_operation_raster(fractp_clipped_raster, fractp_mean_path,
                                     sws_id_list, 'mean', sub_mask, 
                                     fract_mn_dict)
    wyield_mean = create_operation_raster(wyield_clipped_raster, wyield_mean_path,
                                     sws_id_list, 'mean', sub_mask, 
                                     wyield_mn_dict)
    
    #Create area raster so that the volume can be computed.
    wyield_area = create_area_raster(wyield_clipped_raster, wyield_area_path,
                                     sub_sheds, 'subws_id', sub_mask)
    
    def volume(wyield_mn, wyield_area):
        """Vectorized function to compute the water yield volume raster
        
            wyield_mn - numpy array with the water yield mean raster values
            wyield_area - numpy array with the water yield area raster values
            
            returns - water yield volume value """
        if wyield_mn != nodata and wyield_area != nodata:
            return (wyield_mn * wyield_area / 1000)
        else:
            return nodata
        
    #Make blank raster for water yield volume
    wyield_vol_raster = \
        invest_cython_core.newRasterFromBase(wyield_raster, wyield_volume_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
        
    #Get the relevant bands and create water yield volume raster
    wyield_vol_band = wyield_vol_raster.GetRasterBand(1)
    wyield_mean_band = wyield_mean.GetRasterBand(1)
    wyield_area_band = wyield_area.GetRasterBand(1)
    invest_core.vectorize2ArgOp(wyield_mean_band, wyield_area_band, 
                                volume, wyield_vol_band)
    
    #Make blank raster for hectare volume
    wyield_ha_raster = \
        invest_cython_core.newRasterFromBase(wyield_raster, wyield_ha_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
        
    wyield_ha_band = wyield_ha_raster.GetRasterBand(1)

    def ha_vol(wyield_vol, wyield_area):
        """Vectorized function to compute water yield volume in units of ha
        
            wyield_vol - numpy array with the water yield volume raster values
            wyield_area - numpy array with the water yield area raster values
            
            returns - water yield volume in ha value"""

        if wyield_vol != nodata and wyield_area != nodata:
            return wyield_vol / (0.0001 * wyield_area)
        else:
            return nodata
        
    #Make ha volume raster
    invest_core.vectorize2ArgOp(wyield_vol_band, wyield_area_band, ha_vol, 
                                wyield_ha_band)
    
    aet_raster = \
        invest_cython_core.newRasterFromBase(wyield_area, aet_path, 'GTiff', 
                                             nodata, gdal.GDT_Float32)
        
    aet_band = aet_raster.GetRasterBand(1)
    fractp_band = fractp_clipped_raster.GetRasterBand(1)
    fractp_nodata = fractp_band.GetNoDataValue()
    precip_nodata = precip_band.GetNoDataValue()
    
    def aet(fractp, precip):
        """Vectorized function to compute the actual evapotranspiration values
        
            fractp - numpy array with the fractp raster values
            precip - numpy array with the precipitation raster values
            
            returns - actual evapotranspiration values"""
        if fractp != fractp_nodata and precip != precip_nodata:
            return fractp * precip
        else:
            return nodata
    
    invest_core.vectorize2ArgOp(fractp_band, precip_band, aet, aet_band)
    
    #Create the mean actual evapotranspiration raster
    aet_mean = create_operation_raster(aet_raster, aet_mean_path, sws_id_list, 
                                  'mean', sub_mask, mean_dict)
    
    #Create the water yield subwatershed table
    wsr = sheds_map_subsheds(sheds, sub_sheds)
    sub_value_dict = {}
    sub_value_dict['precip_mn'] = \
        get_operation_value(precip_raster, sws_id_list, sub_mask, 'mean')
    sub_value_dict['PET_mn'] = \
        get_operation_value(ape_raster, sws_id_list, sub_mask, 'mean')
    sub_value_dict['AET_mn'] = \
        get_operation_value(aet_raster, sws_id_list, sub_maskj, 'mean')
    sub_value_dict['wyield_mn'] = \
        get_operation_value(wyield_raster, sws_id_list, sub_mask, 'mean')
    sub_value_dict['wyield_sum'] = \
        get_operation_value(wyield_raster, sws_id_list, sub_mask, 'sum')
    
    sub_field_list = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
                      'wyield_mn', 'wyield_sum']
    
    create_writer_table(sub_table_path, sub_field_list, sub_value_dict, wsr)
    
    #Create the water yield watershed table
    value_dict = {}
    value_dict['precip_mn'] = \
        get_operation_value(precip_raster, ws_id_list, shed_mask, 'mean')
    value_dict['PET_mn'] = \
        get_operation_value(ape_raster, ws_id_list, shed_mask, 'mean')
    value_dict['AET_mn'] = \
        get_operation_value(aet_raster, ws_id_list, shed_mask, 'mean')
    value_dict['wyield_mn'] = \
        get_operation_value(wyield_raster, ws_id_list, shed_mask, 'mean')
    value_dict['wyield_sum'] = \
        get_operation_value(wyield_raster, ws_id_list, shed_mask, 'sum')
    
    field_list = ['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 
                  'wyield_sum']
    
    create_writer_table(shed_table_path, field_list, value_dict)
    
def create_writer_table(table_path, field_list, water_dict, wsr=None):
    """Creates a CSV table for the water yield subwatershed and water yield
       watershed
       
       table_path - an output uri string for where the table should be written
       field_list - a list of strings representing the column field headers for
                    the table
       water_dict - a dictionary with keys as strings that corresponds to
                    a dictionary that holds values for the table:
                    water_dict['precip_mn']:{1:650.2, 2:354, 3:908.32, ...}
                    water_dict['AET_mn']:{1:1231, 2:3545.23, 3:809.23, ...}
       wsr - an optional argument whose default value is None. Looking for
             an optional dictionary that holds the relationship between
             watersheds and subwatersheds.
             
       returns - a CSV table"""
       
    table_file = open(table_path, 'wb')
    writer = csv.DictWriter(table_file, field_list)
    field_dict = {}
    #Create a dictionary with field names as keys and the same field name
    #as values, to use as first row in CSV file which will be the column header
    for field in field_list:
        field_dict[field] = field
    #Write column header row
    writer.writerow(field_dict)
    
    #If wsr is not None then we want to write out the subwatershed table   
    if wsr != None:
        for key in water_dict['precip_mn'].iterkeys():
            row_d = {'ws_id':wsr[key],'subws_id':key,
                     'precip_mn':water_dict['precip_mn'][key],
                     'PET_mn':water_dict['PET_mn'][key],
                     'AET_mn':water_dict['AET_mn'][key],
                     'wyield_mn':water_dict['wyield_mn'][key],
                     'wyield_sum':water_dict['wyield_sum'][key]}
            writer.writerow(row_d)
    #If wsr is None then we want to write out the watershed table
    else:
        for key in water_dict['precip_mn'].iterkeys():
            row_d = {'ws_id':key,'precip_mn':water_dict['precip_mn'][key],
                     'PET_mn':water_dict['PET_mn'][key],
                     'AET_mn':water_dict['AET_mn'][key],
                     'wyield_mn':water_dict['wyield_mn'][key],
                     'wyield_sum':water_dict['wyield_sum'][key]}
            writer.writerow(row_d)
        
    return table_file
    
def sheds_map_subsheds(shape, sub_shape):
    """Stores which sub watersheds belong to which watershed
       
       shape - an OGR shapefile of the watersheds
       sub_shape - an OGR shapefile of the sub watersheds
       
       returns - a dictionary where the keys are the sub watersheds id's
                 and whose value is the watersheds id it belongs to
    """
    LOGGER.debug('Starting sheds_map_subsheds')
    layer = shape.GetLayer(0)
    sub_layer = sub_shape.GetLayer(0)
    collection = {}
    #For all the polygons in the watershed check to see if any of the polygons
    #in the sub watershed belong to that watershed by checking the area of the
    #watershed against the area of the Union of the watershed and sub watershed
    #polygon.  The areas will be the same if the sub watershed is part of the
    #watershed and will be different if it is not
    for feat in layer:
        index = feat.GetFieldIndex('ws_id')
        id = feat.GetFieldAsInteger(index)
        geom = feat.GetGeometryRef()
        sub_layer.ResetReading()
        for sub_feat in sub_layer:
            sub_index = sub_feat.GetFieldIndex('subws_id')
            sub_id = sub_feat.GetFieldAsInteger(sub_index)
            sub_geom = sub_feat.GetGeometryRef()
            u_geom = sub_geom.Union(geom)
            #We can't be sure that the areas will be identical because of
            #floating point issues and complete accuracy so we make sure the
            #difference in areas is within reason
            if abs(geom.GetArea() - u_geom.GetArea()) < (math.e**-5):
                collection[sub_id] = id
            
            sub_feat.Destroy()
            
        feat.Destroy()
        
    return collection

def get_operation_value(raster, id_list, shed_mask, operation):
    """Calculates the mean per watershed or sub watershed based on groups of
       pixels from a raster that fall within each watershed or sub watershed
       
       raster - a GDAL raster dataset of the values to find the mean 
       shed_shape - a OGR shapefile of either the watersheds or sub watersheds
       shed_mask - a numpy array that represents the mask for where the 
                   watersheds/sub watersheds fall on the raster
       
       returns - a dictionary whose keys are the sheds id's and values the mean
    """
    LOGGER.debug('Starting get_operation_value')
    band_mean = raster.GetRasterBand(1)
    pixel_data_array = np.copy(band_mean.ReadAsArray())
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    dict = {}

    for id in id_list:
        mask_val = sub_sheds_id_array != id
        set_mask_val = sub_sheds_id_array == id
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        op_val = None
        if operation == 'mean':
            op_val = sum(comp_array) / len(comp_array)
        else:
            op_val = sum(comp_array)
        dict[id] = op_val
        
    return dict

def get_mask(raster, path, shed_shape, field_name):
    """Creates a copy of a raster and fills it with nodata values.  It then
       rasterizes the id field from shed_shape onto that raster and returns
       a numpy array representation of the raster
       
       raster - a GDAL raster dataset that has the desired pixel size and
                dimensions
       path - a uri string path for the creation of the copied raster
       shed_shape - an OGR shapefile, either watershed or sub watershed
       field_name - a string of the field name from shed_shape to rasterize
       
       returns - a numpy array representation of the rasterized shapes id 
                 values
    """
    LOGGER.debug('Starting get_mask')
    raster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    band.Fill(-1)
    attribute_string = 'ATTRIBUTE=' + field_name
    gdal.RasterizeLayer(raster, [1], shed_shape.GetLayer(0),
                        options = [attribute_string])
    sub_sheds_id_array = band.ReadAsArray()
    
    return sub_sheds_id_array

def get_shed_ids(arr, nodata):
    tmp_ar = np.copy(arr)
    tmp_aru = np.unique(tmp_ar.flatten())
    tmp_ard = np.delete(tmp_aru, np.where(tmp_aru == nodata))
    return tmp_ard
    
def create_area_raster(raster, path, shed_shape, field_name, shed_mask):
    """Creates a new raster representing the area per watershed or per
       sub watershed 
    
       raster - a GDAL raster dataset that has the desired pixel size and
                dimensions
       path - a uri string path for the creation of the area raster
       shed_shape - an OGR shapefile, either watershed or sub watershed
       field_name - a string of the id field from shed_shape
       shed_mask - a numpy array representing the shed/sub shed id mask
       
       returns - a raster       
    """
    LOGGER.debug('Starting create_area_raster')
    raster_area = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band_area = raster_area.GetRasterBand(1)
    pixel_data_array = band_area.ReadAsArray()
    nodata = band_area.GetNoDataValue()
    band_area.Fill(nodata)
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    layer = shed_shape.GetLayer(0)
    layer.ResetReading()
    for feat in layer:
        geom = feat.GetGeometryRef()
        geom_type = geom.GetGeometryType()
        index = feat.GetFieldIndex(field_name)
        value = feat.GetFieldAsInteger(index)
        mask_val = sub_sheds_id_array != value
        set_mask_val = sub_sheds_id_array == value
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        np.putmask(new_data_array, set_mask_val, geom.GetArea())
        
    band_area.WriteArray(new_data_array, 0, 0)  
    return raster_area

def create_operation_raster(raster, path, id_list, operation, shed_mask, dict):
    """Creates a new raster representing the mean per watershed or per
       sub watershed 
    
       raster - a GDAL raster dataset that has the desired pixel size and
                dimensions as well as the values we want to take the mean of
       path - a uri string path for the creation of the mean raster
       shed_shape - an OGR shapefile, either watershed or sub watershed
       field_name - a string of the id field from shed_shape
       shed_mask - a numpy array representing the shed/sub shed id mask
       
       returns - a raster       
    """
    LOGGER.debug('Starting create_operation_raster')
    raster_op = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band_op = raster_op.GetRasterBand(1)
    nodata = band_op.GetNoDataValue()
    pixel_data_array = band_op.ReadAsArray()
    pixel_data_array_nodata = np.where(pixel_data_array == nodata, 0, pixel_data_array)
    band_op.Fill(nodata)
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)

    for id in id_list:
        mask_val = sub_sheds_id_array != id
        set_mask_val = sub_sheds_id_array == id
        masked_array = np.ma.array(pixel_data_array_nodata, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        op_val = None
        if operation == 'mean':
            op_val = sum(comp_array) / len(comp_array)
        else:
            op_val = sum(comp_array)
        np.putmask(new_data_array, set_mask_val, op_val)
        dict[id] = op_val
        
    band_op.WriteArray(new_data_array, 0, 0)
    return raster_op

def clip_raster_from_polygon(shape, raster, path):
    """Returns a raster where any value outside the bounds of the
    polygon shape are set to nodata values. This represents clipping 
    the raster to the dimensions of the polygon.
    
    shape - A polygon shapefile representing the bounds for the raster
    raster - A raster to be bounded by shape
    path - The path for the clipped output raster
    
    returns - The clipped raster    
    """
    shape.GetLayer(0).ResetReading()
    #Create a new raster as a copy from 'raster'
    copy_raster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    copy_band = copy_raster.GetRasterBand(1)
    #Set the copied rasters values to nodata to create a blank raster.
    nodata = copy_band.GetNoDataValue()
    LOGGER.debug('nodata: %s', nodata)
    copy_band.Fill(nodata)
    #Rasterize the polygon layer onto the copied raster
    gdal.RasterizeLayer(copy_raster, [1], shape.GetLayer(0))
    def fill_bound_data(value, copy_value):
        """If the copied raster's value is nodata then the pixel is not within
        the polygon and should write nodata back. If copied raster's value
        is not nodata, then pixel lies within polygon and the value 
        from 'raster' should be written out.
        
        value - The pixel value of the raster to be bounded by the shape
        copy_value - The pixel value of a copied raster where every pixel
                     is nodata except for where the polygon was rasterized
        
        returns - Either a nodata value or relevant pixel value
        """
        if copy_value == nodata:
            return copy_value
        else:
            return value
    #Vectorize the two rasters using the operation fill_bound_data
    invest_core.vectorize2ArgOp(raster.GetRasterBand(1), copy_band, \
                                fill_bound_data, copy_band)
    return copy_raster
    
def raster_from_table_values(base_raster, new_path, bio_dict, field):
    """Creates a new raster from 'base_raster' whose values are data from a 
       dictionary that directly relates to the pixel value from 'base_raster'
    
       base_raster - a GDAL raster dataset whose pixel values relate to the 
                     keys in 'bio_dict'
       new_path - a uri string for where the new raster should be written
       bio_dict - a dictionary representing the biophysical csv table, whose
                  keys are the lulc codes and whose values are the etk and root
                  depth values.
                  bio_dict[1] = {'etk':500, 'root_depth':700}
                  bio_dict[11] = {'etk':100, 'root_depth':10}...
                  
       field - a string of which field in the table to use as the new raster
               pixel values
       
       returns - a GDAL raster
    """
    LOGGER.debug('Starting raster_from_table_values')
    base_band = base_raster.GetRasterBand(1)
    base_nodata = base_band.GetNoDataValue()
    array = base_band.ReadAsArray()

    tmp_raster = \
        invest_cython_core.newRasterFromBase(base_raster, new_path, 'GTiff', 
                                             base_nodata, gdal.GDT_Float32)
    
    #http://stackoverflow.com/questions/3403973/fast-replacement-of-values-in-a-numpy-array
    new_array = array.astype(np.float)
    
    for k, v in bio_dict.iteritems(): 
        #For all the lulc codes in the dictionary, if the lulc code is found
        #on the lulc raster, then replace that value with the corresponding
        #desired value, else replace that value with a nodata value.
        if (array==int(k)).any():
            #array==int(k) provides a truth mask, so new_array[array==int(k)] 
            #is saying to replace all of the values that are true with 
            #float(v[field])
            new_array[array==int(k)] = float(v[field])
        else:
            new_array[array==int(k)] = base_nodata
            
    #Write the newly developed numpy array to the raster band
    tmp_band = tmp_raster.GetRasterBand(1)
    tmp_band.WriteArray(new_array, 0, 0)
    
    return tmp_raster

def water_scarcity(args):
    """Executes the water scarcity model
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['water_yield_vol'] - a GDAL raster dataset, generated from
            the water_yield model, describing the total water yield per
            sub-watershed. The approximate absolute annual water yield across
            the landscape (cubic meters) (required) 
        args['water_yield_mn'] - a GDAL raster dataset, generated from
            the water_yield model, describing the mean water yield per
            sub-watershed (mm) (required)
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
    
    #Construct folder paths
    workspace_dir = args['workspace_dir']
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'
    
    #Get arguments
    demand_dict = args['demand_table']
    lulc_raster = args['lulc']
    calib_dict = args['hydro_calibration_table']
    wyield_vol_raster = args['water_yield_vol']
    watersheds = args['watersheds']
    sub_sheds = args['sub_watersheds']
    water_shed_table = args['watershed_yield_table']
    sub_shed_table = args['subwatershed_yield_table']
    wyield_mean = args['water_yield_mn']
        
    #Suffix handling
    suffix = args['results_suffix']
    if len(suffix) > 0:
        suffix_tif = '_' + suffix + '.tif'
        suffix_csv = '_' + suffix + '.csv'
    else:
        suffix_tif = '.tif'
        suffix_csv = '.csv'
        
    #Path for the calibrated water yield volume per sub-watershed
    wyield_calib_path = output_dir + os.sep + 'cyield_vol' + suffix_tif
    #Path for mean and total water consumptive volume
    consump_vol_path = output_dir + os.sep + 'consum_vol' + suffix_tif
    consump_mean_path = output_dir + os.sep + 'consum_mn' + suffix_tif
    clipped_consump_path = \
        intermediate_dir + os.sep + 'clipped_consump' + suffix_tif
    #Paths for realized and mean realized water supply volume
    rsupply_vol_path = output_dir + os.sep + 'rsup_vol' + suffix_tif
    rsupply_mean_path = output_dir + os.sep + 'rsup_mn' + suffix_tif
    #Paths for watershed and sub watershed scarcity tables
    ws_out_table_name = \
        output_dir + os.sep + 'water_scarcity_watershed' + suffix_csv 
    sws_out_table_name = \
        output_dir + os.sep + 'water_scarcity_subwatershed' + suffix_csv
    #Paths for sub watershed masks
    sub_mask_raster_path = intermediate_dir + os.sep + 'sub_shed_mask2.tif'
    sub_mask_raster_path2 = intermediate_dir + os.sep + 'sub_shed_mask3.tif'
    
    #The nodata value to use for the output rasters
    nodata = -1
    
    #Create watershed mask raster
    ws_mask = invest_cython_core.newRasterFromBase(wyield_vol_raster, '', 'MEM', 
                                                   nodata, gdal.GDT_Float32)

    gdal.RasterizeLayer(ws_mask, [1], watersheds.GetLayer(0),
                        options = ['ATTRIBUTE=ws_id'])
    
    #Multiply calibration with wyield_vol raster to get cyield_vol
    
    nodata_vol = wyield_vol_raster.GetRasterBand(1).GetNoDataValue()
    
    def cyield_vol_op(wyield_vol, calib):
        """Function that computes the cyield volume
        
           wyield_vol - 
           calib - 
           
           returns - 
        """
        if wyield_vol != nodata_vol and calib != nodata:
            return wyield_vol * int(calib_dict[str(int(calib))])
        else:
            return nodata
        
    wyield_calib = \
        invest_cython_core.newRasterFromBase(ws_mask, wyield_calib_path,
                                             'GTiff', nodata, gdal.GDT_Float32)
        
    ws_band = ws_mask.GetRasterBand(1)
    wyield_calib_band = wyield_calib.GetRasterBand(1)
    wyield_vol_band = wyield_vol_raster.GetRasterBand(1)
    
    invest_core.vectorize2ArgOp(wyield_vol_band, ws_band, cyield_vol_op, 
                                wyield_calib_band)
    
    #Create raster from land use raster, subsituting in demand value
    
    lulc_band = lulc_raster.GetRasterBand(1)
    lulc_nodata = lulc_band.GetNoDataValue()
    tmp_consump = invest_cython_core.newRasterFromBase(lulc_raster, '', 'MEM', 
                                                       nodata, gdal.GDT_Float32)
    tmp_consump_band = tmp_consump.GetRasterBand(1)
    
    def lulc_demand(lulc):
        """Function that maps demand values to the corresponding lulc_id
        
           lulc - 
           
           returns - 
        """
        if str(lulc) in demand_dict:
            return int(demand_dict[str(lulc)]['demand'])
        else:
            return nodata
    
    invest_core.vectorize1ArgOp(lulc_band, lulc_demand, tmp_consump_band)
    
    clipped_consump = clip_raster_from_polygon(watersheds, tmp_consump, 
                                               clipped_consump_path)
    
    #Take sum of consump over sub watersheds making consump_vol
    
    #Get a numpy array from rasterizing the sub watershed id values into
    #a raster. The numpy array will be the sub watershed mask used for
    #calculating mean and sum values at a sub watershed basis
    sub_mask = get_mask(clipped_consump, sub_mask_raster_path, sub_sheds, 
                        'subws_id')
    sws_id_list = get_shed_ids(sub_mask, nodata)
    LOGGER.debug('shed_id_list : %s', sws_id_list)
    
    sum_dict = {}
    sum_raster = \
        create_operation_raster(clipped_consump, consump_vol_path, sws_id_list, 
                          'sum', sub_mask, sum_dict)
        
    LOGGER.debug('sum_dict : %s', sum_dict)
    
    #Take mean of consump over sub watersheds making conusmp_mean
    mean_dict = {}
    mean_raster = \
        create_operation_raster(clipped_consump, consump_mean_path, sws_id_list, 
                           'mean', sub_mask, mean_dict)
    LOGGER.debug('mean_dict : %s', mean_dict)
    #Make rsupply_vol by wyield_calib minus consump_vol

    nodata_calib = wyield_calib.GetRasterBand(1).GetNoDataValue()
    nodata_consump = sum_raster.GetRasterBand(1).GetNoDataValue()

    def rsupply_vol_op(wyield_calib, consump_vol):
        """Function that computes the rsupply volume
        
           wyield_calib - 
           consump_vol - 
           
           returns - 
        """
        if (wyield_calib != nodata_calib and consump_vol != nodata_consump):
            return wyield_calib - consump_vol
        else:
            return 0
        
    vop = np.vectorize(rsupply_vol_op)

    invest_core.vectorizeRasters([wyield_calib, sum_raster], vop, 
                                 rasterName=rsupply_vol_path)
    
    #Make rsupply_mean by wyield_mean minus consump_mean
    
    
    def rsupply_mean_op(wyield_mean, consump_mean):
        """Function that computes the mean rsupply
        
           wyield_mean - 
           consump_mean - 
           
           returns - 
        """
        return wyield_mean - consump_mean

    invest_core.vectorizeRasters([wyield_mean, mean_raster], rsupply_mean_op, 
                                 rasterName=rsupply_mean_path)
    
    #Make sub watershed and watershed tables by adding values onto the tables
    #provided from sub watershed yield and watershed yield
    sub_mask2 = get_mask(wyield_calib, sub_mask_raster_path2, sub_sheds, 
                         'subws_id')
    sws_id_list2 = get_shed_ids(sub_mask2, nodata)
    
    #cyielc_vl per watershed
    shed_subshed_map = {}
    for key, val in sub_shed_table.iteritems():
        if val['ws_id'] in shed_subshed_map:
            shed_subshed_map[val['ws_id']].append(key)
        else:
            shed_subshed_map[val['ws_id']] = [key]
            
    LOGGER.debug('shed_subshed_map : %s', shed_subshed_map) 
    
    new_keys_ws = {}
    new_keys_sws = {}
    
    field_name = 'ws_id'
    cyield_d = get_operation_value(wyield_calib, sws_id_list2, sub_mask2, 'mean')
    cyield_vol_d = sum_mean_dict(shed_subshed_map, cyield_d, 'sum')
    new_keys_ws['cyield_vl'] = cyield_vol_d
    new_keys_sws['cyield_vl'] = cyield_d
    
    #consump_vl per watershed
    consump_vl_d = sum_mean_dict(shed_subshed_map, sum_dict, 'sum')
    new_keys_ws['consump_vl'] = consump_vl_d
    new_keys_sws['consump_vl'] = sum_dict
    
    #consump_mean per watershed
    consump_mn_d = sum_mean_dict(shed_subshed_map, mean_dict, 'mean')
    new_keys_ws['consump_mn'] = consump_mn_d
    new_keys_sws['consump_mn'] = mean_dict
    
    #rsupply_vl per watershed
    rsupply_vl_raster = gdal.Open(rsupply_vol_path)
    field_name = 'ws_id'
    rsupply_vl_d = get_operation_value(rsupply_vl_raster, sws_id_list2, sub_mask2, 'mean')
    rsupply_vl_dt = sum_mean_dict(shed_subshed_map, rsupply_vl_d, 'sum')
    new_keys_ws['rsupply_vl'] = rsupply_vl_dt
    new_keys_sws['rsupply_vl'] = rsupply_vl_d
    
    #rsupply_mn per watershed
    rsupply_mn_raster = gdal.Open(rsupply_mean_path)
    field_name = 'ws_id'
    rsupply_mn_d = get_operation_value(rsupply_mn_raster, sws_id_list2, sub_mask2, 'mean')
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
    LOGGER.debug('updated ws table : %s', water_shed_table)
    
    for key, val in sub_shed_table.iteritems():
        for index, item in new_keys_sws.iteritems():
            val[index] = item[int(key)]
    LOGGER.debug('updated sws table : %s', sub_shed_table)
    
    write_scarcity_table(water_shed_table, field_list_ws, ws_out_table_name)
    write_scarcity_table(sub_shed_table, field_list_sws, sws_out_table_name)
    
def write_scarcity_table(shed_table, field_list, file_path):
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
    #Create a dictionary with field names as keys and the same field name
    #as values, to use as first row in CSV file which will be the column header
    for field in field_list:
        field_dict[field] = field
    #Write column header row
    writer.writerow(field_dict)
    
    for key, dict in shed_table.iteritems():
        writer.writerow(dict)
    
    shed_file.close()

def sum_mean_dict(dict1, dict2, op):
    """
    
       dict1 - a dictionary whose keys are the watershed id's, which point to
               a python list whose values are the sub wateshed id's that fall
               within that watershed
       dict2 - a dictionary whose keys are sub watershed id's and
               whose values are the desired numbers to be summed or meaned
       op - a string indicating which operation to do ('sum' or 'mean')
       
       returns - a dictionary
    """
    new_dict = {}
    for key, val in dict1.iteritems():
        sum_ws = 0
        counter = 0
        for item in val:
            counter = counter + 1
            sum_ws = sum_ws + dict2[int(item)]
        if op == 'sum':
            new_dict[key] = sum_ws
        else:
            new_dict[key] = sum_ws / counter
    
    LOGGER.debug('sum_ws_dict rsupply_mean: %s', new_dict)
    return new_dict

def valuation(args):
    """This function invokes the valuation model for hydropower
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['cal_water_yield'] - a Gdal raster of the calibrated
            water yield volume per sub-watershed, generated as an output
            of the water scarcity model (required)
        args['water_consump'] - a Gdal raster of the total water
            consumptive use for each sub-watershed, generated as an output
            of the water scarcity model (required)
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
            hydropower stations with associated model values (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional) 
           
        returns - nothing"""
        
    #water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')
    
    #Construct folder paths
    workspace_dir = args['workspace_dir']
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'
    
    #Get arguments
    watersheds = args['watersheds']
    sub_sheds = args['sub_watersheds']
    ws_scarcity_table = args['watershed_scarcity_table']
    sws_scarcity_table = args['subwatershed_scarcity_table']
    valuation_table = args['valuation_table']
    
    #Suffix handling
    suffix = args['results_suffix']
    if len(suffix) > 0:
        suffix_tif = '_' + suffix + '.tif'
        suffix_csv = '_' + suffix + '.csv'
    else:
        suffix_tif = '.tif'
        suffix_csv = '.csv'
    
    #Paths for the watershed and subwatershed tables
    watershed_value_table = \
        output_dir + os.sep + 'hydropower_value_watershed' + suffix_csv
    subwatershed_value_table = \
        output_dir + os.sep + 'hydropower_value_subwatershed' + suffix_csv
    #Paths for the hydropower value raster
    hp_val_tmppath = output_dir + os.sep + 'hp_val_tmp' + suffix_tif
    hp_val_path = output_dir + os.sep + 'hp_val' + suffix_tif
    #Paths for the hydropower energy raster
    hp_energy_tmppath = output_dir + os.sep + 'hp_energy_tmp' + suffix_tif
    hp_energy_path = output_dir + os.sep + 'hp_energy' + suffix_tif
    
    energy_dict = {}
    npv_dict = {}
    
    for key in ws_scarcity_table.keys():
        val_row = valuation_table[key]
        ws_row = ws_scarcity_table[key]
        efficiency = float(val_row['efficiency'])
        fraction = float(val_row['fraction'])
        height = float(val_row['height'])
        rsupply_vl = float(ws_row['rsupply_vl'])
        
        energy = efficiency * fraction * height * rsupply_vl * 0.00272
        energy_dict[key] = energy
        
        time = float(val_row['time_span'])
        kwval = float(val_row['kw_price'])
        disc = float(val_row['discount'])
        cost = float(val_row['cost'])
        
        dsum = 0
        
        for t in range (0, time):
            dsum = dsum + (1 / np.square(1 + (disc / 100)))
            
        NPV = ((kwval * energy) - cost) * dsum
        npv_dict[key] = NPV
        ws_scarcity_table[key]['hp_value'] = NPV
        ws_scarcity_table[key]['hp_energy'] = energy
        
    LOGGER.debug('energy dict : %s', energy_dict)
    LOGGER.debug('npv dict : %s', npv_dict)

    #NPV for sub shed is NPV for water shed times ratio of rsupply_vl of 
    #sub shed to rsupply_vl of water shed
    sws_npv_dict = {}
    sws_energy_dict = {}
    
    for key, val in sws_scarcity_table.iteritems():
        ws_id = val['ws_id']
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
    
    
    write_scarcity_table(ws_scarcity_table, field_list_ws, \
                         watershed_value_table)
    write_scarcity_table(sws_scarcity_table, field_list_sws, \
                         subwatershed_value_table)
    
    
    invest_cython_core.createRasterFromVectorExtents(30, 30, gdal.GDT_Float32, 
                                                     -1, hp_val_tmppath, 
                                                     sub_sheds)
    
    invest_cython_core.createRasterFromVectorExtents(30, 30, gdal.GDT_Float32, 
                                                     -1, hp_val_path, sub_sheds)
    
    hp_val = gdal.Open(hp_val_path, gdal.GA_Update)
    hp_val_tmp = gdal.Open(hp_val_tmppath, gdal.GA_Update)
    
    gdal.RasterizeLayer(hp_val_tmp, [1], sub_sheds.GetLayer(0),
                        options = ['ATTRIBUTE=subws_id'])
    
    def npv_op(hp_val):
        if hp_val != -1:
            return sws_npv_dict[str(int(hp_val))]
        else:
            return -1
        
    hp_val_band = hp_val.GetRasterBand(1)
    hp_val_band_tmp = hp_val_tmp.GetRasterBand(1)    
    
    invest_core.vectorize1ArgOp(hp_val_band_tmp, npv_op, hp_val_band)
    
    invest_cython_core.createRasterFromVectorExtents(30, 30, gdal.GDT_Float32, 
                                                     -1, hp_energy_tmppath, 
                                                     sub_sheds)
    
    invest_cython_core.createRasterFromVectorExtents(30, 30, gdal.GDT_Float32, 
                                                     -1, hp_energy_path, 
                                                     sub_sheds)
    
    hp_energy = gdal.Open(hp_energy_path, gdal.GA_Update)
    hp_energy_tmp = gdal.Open(hp_energy_tmppath, gdal.GA_Update)
    
    gdal.RasterizeLayer(hp_energy_tmp, [1], sub_sheds.GetLayer(0),
                        options = ['ATTRIBUTE=subws_id'])
    
    def energy_op(energy_val):
        if energy_val != -1:
            return sws_energy_dict[str(int(energy_val))]
        else:
            return -1
        
    hp_energy_band = hp_energy.GetRasterBand(1)
    hp_energy_band_tmp = hp_energy_tmp.GetRasterBand(1)    
    
    invest_core.vectorize1ArgOp(hp_energy_band_tmp, energy_op, hp_energy_band)