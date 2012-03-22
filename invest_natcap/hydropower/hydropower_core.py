"""Module that contains the core computational components for the hydropower
    model including the water yield, water scarcity , and valuation functions"""

import logging
import os
import csv
import math

import numpy as np
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('sediment_core')

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
        args['ape'] - an input raster describing the 
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
        args['zhang'] - floating point value between 1 and 10 corresponding
            to the seasonal distribution of precipitation (required)
            
        returns nothing"""
        
    LOGGER.info('Starting Water Yield Calculation')

    workspace_dir = args['workspace_dir']
    #Construct folder paths
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'
    #Get inputs from the args dictionary
    bio_dict = args['biophysical_dictionary']
    lulc_raster = args['lulc']
    ape_raster = args['ape']
    precip_raster = args['precipitation']
    soil_depth_raster = args['soil_depth']
    pawc_raster = args['pawc']
    sub_sheds = args['sub_watersheds']
    sheds = args['watersheds']
    zhang = float(args['zhang'])
    
    #Create etk raster from table values to use in future calculations
    tmp_etk_path = intermediate_dir + os.sep + 'tmp_etk.tif'
    tmp_etk_raster = create_etk_root_rasters(lulc_raster, tmp_etk_path, 255.0,
                                             bio_dict, 'etk')
    
    #Create root raster from table values to use in future calculations
    tmp_root_path = intermediate_dir + os.sep + 'tmp_root.tif'
    tmp_root_raster = create_etk_root_rasters(lulc_raster, tmp_root_path, 255.0,
                                             bio_dict, 'root_depth')
    
    def fractp(etk, ape, precip, root, soil, pawc):
        """Vectorized function that calculates the fractp raster
        
            etk - numpy array with the etk raster values
            ape - numpy array with the potential evapotranspiration raster 
                  values
            precip - numpy array with the precipitation raster values
            root - numpy array with the root raster values
            soil - numpy array with the soil depth raster values
            pawc - numpy array with the plant available water content raster 
                   values
            
        returns - fractp value"""
        
        val = (etk * ape) / 1000
        tmp_DI = val / precip
        
        awc = (np.minimum(root, soil) * pawc)
        
        tmp_w = (awc / (precip + 1)) * zhang
        
        tmp_max_aet = np.copy(tmp_DI)
        #Replace any value greater than 1 with 1
        np.putmask(tmp_max_aet, tmp_max_aet > 1, 1)
        
        tmp_calc = \
            ((tmp_w * tmp_DI + 1) / (( 1 / tmp_DI) + (tmp_w * tmp_DI + 1)))
        fractp = np.minimum(tmp_max_aet, tmp_calc)
        return fractp
    
    #Create the fractp raster
    fractp_path = intermediate_dir + os.sep + 'fractp.tif'
    raster_list = [tmp_etk_raster, ape_raster, precip_raster, tmp_root_raster,
                   soil_depth_raster, pawc_raster]
    fractp_raster = \
        invest_core.vectorizeRasters(raster_list, fractp, rasterName=fractp_path)
    
    def wyield(fractp, precip):
        """Vectorized function that calculates the water yeild raster
        
           fractp - numpy array with the fractp raster values
           precip - numpy array with the precipitation raster values
           
           returns - water yield value"""
           
        return (1 - fractp) * precip
    
    #Create the water yield raster 
    wyield_path = intermediate_dir + os.sep + 'wyield.tif'
    wyield_raster = \
        invest_cython_core.newRasterFromBase(fractp_raster, wyield_path, 
                                            'GTiff', -1, gdal.GDT_Float32)
        
    #Get relevant raster bands for creating water yield raster
    fractp_band = fractp_raster.GetRasterBand(1)
    precip_band = precip_raster.GetRasterBand(1)
    wyield_band = wyield_raster.GetRasterBand(1)
    
    invest_core.vectorize2ArgOp(fractp_band, precip_band, wyield, wyield_band)
    
    #Paths for clipping the fractp/wyield raster to watershed polygons
    fractp_clipped_path = intermediate_dir + os.sep + 'fractp_clipped.tif'
    wyield_clipped_path = intermediate_dir + os.sep + 'wyield_clipped.tif'
    
    #Clip fractp/wyield rasters to watershed polygons
    wyield_clipped_raster = clip_raster_from_polygon(sheds, wyield_raster, \
                                                     wyield_clipped_path)
    fractp_clipped_raster = clip_raster_from_polygon(sheds, fractp_raster, \
                                                     fractp_clipped_path)
    #Create paths for the mean/volume rasters
    fractp_mean_path = intermediate_dir + os.sep + 'fractp_mn.tif'
    wyield_mean_path = intermediate_dir + os.sep + 'wyield_mn.tif'
    wyield_area_path = intermediate_dir + os.sep + 'wyield_area.tif'
    wyield_volume_path = intermediate_dir + os.sep + 'wyield_volume.tif'
    wyield_ha_path = intermediate_dir + os.sep + 'wyield_ha.tif'
    
    #Get a numpy array from rasterizing the sub watershed id values into
    #a raster. The numpy array will be the sub watershed mask used for
    #calculating mean and sum values at a sub watershed basis
    sub_mask_raster_path = intermediate_dir + os.sep + 'sub_shed_mask.tif'
    sub_mask = get_mask(fractp_clipped_raster, sub_mask_raster_path,
                               sub_sheds, 'subws_id')
    #Get a numpy array from rasterizing the watershed id values into
    #a raster. The numpy array will be the watershed mask used for
    #calculating mean and sum values at a per watershed basis
    shed_mask_raster_path = intermediate_dir + os.sep + 'shed_mask.tif'
    shed_mask = get_mask(fractp_clipped_raster, shed_mask_raster_path,
                               sheds, 'ws_id')
    
    #Create mean rasters for fractp and water yield
    fractp_mean = create_mean_raster(fractp_clipped_raster, fractp_mean_path,
                                     sub_sheds, 'subws_id', sub_mask)
    wyield_mean = create_mean_raster(wyield_clipped_raster, wyield_mean_path,
                                     sub_sheds, 'subws_id', sub_mask)
    
    #Create area raster so that the volume can be computed.
    wyield_area = create_area_raster(wyield_clipped_raster, wyield_area_path,
                                     sub_sheds, 'subws_id', sub_mask)
    
    def volume(wyield_mn, wyield_area):
        """Vectorized function to compute the water yield volume raster
        
            wyield_mn - numpy array with the water yield mean raster values
            wyield_area - numpy array with the water yield area raster values
            
            returns - water yield volume value """
            
        return (wyield_mn * wyield_area / 1000)
    
    #Make blank raster for water yield volume
    wyield_vol_raster = \
        invest_cython_core.newRasterFromBase(wyield_raster, wyield_volume_path, 
                                            'GTiff', -1, gdal.GDT_Float32)
        
    #Get the relevant bands and create water yield volume raster
    wyield_vol_band = wyield_vol_raster.GetRasterBand(1)
    wyield_mean_band = wyield_mean.GetRasterBand(1)
    wyield_area_band = wyield_area.GetRasterBand(1)
    invest_core.vectorize2ArgOp(wyield_mean_band, wyield_area_band, 
                                volume, wyield_vol_band)
    
    #Make blank raster for hectare volume
    wyield_ha_raster = \
        invest_cython_core.newRasterFromBase(wyield_raster, wyield_ha_path, 
                                            'GTiff', -1, gdal.GDT_Float32)
        
    wyield_ha_band = wyield_ha_raster.GetRasterBand(1)

    def ha_vol(wyield_vol, wyield_area):
        """Vectorized function to compute water yield volume in units of ha
        
            wyield_vol - numpy array with the water yield volume raster values
            wyield_area - numpy array with the water yield area raster values
            
            returns - water yield volume in ha value"""

        if wyield_vol == 0.0 and wyield_area == 0.0:
            return 0.0
        else:
            return wyield_vol / (0.0001 * wyield_area)
        
    #Make ha volume raster
    invest_core.vectorize2ArgOp(wyield_vol_band, wyield_area_band, ha_vol, 
                                wyield_ha_band)
    
    #Create aet and aet mean raster
    aet_path = intermediate_dir + os.sep + 'aet.tif'
    aet_mean_path = intermediate_dir + os.sep + 'aet_mn.tif'
    
    aet_raster = \
        invest_cython_core.newRasterFromBase(wyield_area, aet_path, 
                                            'GTiff', -1, gdal.GDT_Float32)
        
    aet_band = aet_raster.GetRasterBand(1)
    fractp_band = fractp_clipped_raster.GetRasterBand(1)
    
    def aet(fractp, precip):
        """Vectorized function to compute the actual evapotranspiration values
        
            fractp - numpy array with the fractp raster values
            precip - numpy array with the precipitation raster values
            
            returns - actual evapotranspiration values"""
            
        return fractp * precip
    
    invest_core.vectorize2ArgOp(fractp_band, precip_band, aet, aet_band)
    
    #Create the mean actual evapotranspiration raster
    aet_mean = create_mean_raster(aet_raster, aet_mean_path,
                                  sub_sheds, 'subws_id', sub_mask)
    
    #Create the water yield subwatershed table
    sub_table_path = intermediate_dir + os.sep + 'water_yield_subwatershed.csv'
    wsr = polygon_contains_polygons(sheds, sub_sheds)
    sub_value_dict = {}
    sub_value_dict['precip_mn'] = \
        get_mean(precip_raster, sub_sheds, 'subws_id', sub_mask)
    sub_value_dict['PET_mn'] = \
        get_mean(ape_raster, sub_sheds, 'subws_id', sub_mask)
    sub_value_dict['AET_mn'] = \
        get_mean(aet_raster, sub_sheds, 'subws_id', sub_mask)
    sub_value_dict['wyield_mn'] = \
        get_mean(wyield_raster, sub_sheds, 'subws_id', sub_mask)
    sub_value_dict['wyield_sum'] = \
        get_sum(wyield_raster, sub_sheds, 'subws_id', sub_mask)
    sub_field_list = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
                      'wyield_mn', 'wyield_sum']
    
    create_writer_table(sub_table_path, sub_field_list, sub_value_dict, wsr)
    
    #Create the water yield watershed table
    shed_table_path = intermediate_dir + os.sep + 'water_yield_watershed.csv'
    value_dict = {}
    value_dict['precip_mn'] = get_mean(precip_raster, sheds, 'ws_id', shed_mask)
    value_dict['PET_mn'] = get_mean(ape_raster, sheds, 'ws_id', shed_mask)
    value_dict['AET_mn'] = get_mean(aet_raster, sheds, 'ws_id', shed_mask)
    value_dict['wyield_mn'] = get_mean(wyield_raster, sheds, 'ws_id', shed_mask)
    value_dict['wyield_sum'] = get_sum(wyield_raster, sheds, 'ws_id', shed_mask)
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
    
    write_table_rows(water_dict, writer, wsr)
    
    return table_file

def write_table_rows(water_dict, writer, wsr):
    """
    """
    if wsr != None:
        for key in water_dict['precip_mn'].iterkeys():
            row_d = {'ws_id':wsr[key],'subws_id':key,
                     'precip_mn':water_dict['precip_mn'][key],
                     'PET_mn':water_dict['PET_mn'][key],
                     'AET_mn':water_dict['AET_mn'][key],
                     'wyield_mn':water_dict['wyield_mn'][key],
                     'wyield_sum':water_dict['wyield_sum'][key]}
            writer.writerow(row_d)
    
    else:
        for key in water_dict['precip_mn'].iterkeys():
            row_d = {'ws_id':key,'precip_mn':water_dict['precip_mn'][key],
                     'PET_mn':water_dict['PET_mn'][key],
                     'AET_mn':water_dict['AET_mn'][key],
                     'wyield_mn':water_dict['wyield_mn'][key],
                     'wyield_sum':water_dict['wyield_sum'][key]}
            writer.writerow(row_d)
        
def polygon_contains_polygons(shape, sub_shape):
    """
    """
    layer = shape.GetLayer(0)
    sub_layer = sub_shape.GetLayer(0)
    collection = {}
    
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
            if abs(geom.GetArea() - u_geom.GetArea()) < (math.e**-5):
                collection[sub_id] = id
            
            sub_feat.Destroy()
            
        feat.Destroy()
        
    return collection


def get_mean(raster, sub_sheds, field_name, shed_mask):
    """
    """
    band_mean = raster.GetRasterBand(1)
    pixel_data_array = np.copy(band_mean.ReadAsArray())
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    dict = {}
    sub_sheds.GetLayer(0).ResetReading()
    for feat in sub_sheds.GetLayer(0):
        index = feat.GetFieldIndex(field_name)
        value = feat.GetFieldAsInteger(index)
        mask_val = sub_sheds_id_array != value
        set_mask_val = sub_sheds_id_array == value
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        mean = sum(comp_array) / len(comp_array)
        dict[value] = mean
        feat.Destroy()
        
    return dict

def get_sum(raster, sub_sheds, field_name, shed_mask):
    """
    """
    band_mean = raster.GetRasterBand(1)
    pixel_data_array = np.copy(band_mean.ReadAsArray())
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    dict = {}
    sub_sheds.GetLayer(0).ResetReading()
    for feat in sub_sheds.GetLayer(0):
        index = feat.GetFieldIndex(field_name)
        value = feat.GetFieldAsInteger(index)
        mask_val = sub_sheds_id_array != value
        set_mask_val = sub_sheds_id_array == value
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        mean = sum(comp_array)
        dict[value] = mean
        feat.Destroy()
        
    return dict

def get_mask(raster, path, sub_sheds, field_name):
    """
    """
    
    raster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    band.Fill(-1)
    attribute_string = 'ATTRIBUTE=' + field_name
    gdal.RasterizeLayer(raster, [1], sub_sheds.GetLayer(0),
                        options = [attribute_string])
    sub_sheds_id_array = band.ReadAsArray()
    
    return sub_sheds_id_array
    
def create_area_raster(raster, path, sub_sheds, field_name, shed_mask):
    """
    """
    raster_area = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band_area = raster_area.GetRasterBand(1)
    pixel_data_array = band_area.ReadAsArray()
    nodata = band_area.GetNoDataValue()
    band_area.Fill(nodata)
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    
    for feat in sub_sheds.GetLayer(0):
        geom = feat.GetGeometryRef()
        geom_type = geom.GetGeometryType()
        LOGGER.debug('AREA OF Poly : %s', geom.GetArea())
        index = feat.GetFieldIndex(field_name)
        value = feat.GetFieldAsInteger(index)
        mask_val = sub_sheds_id_array != value
        set_mask_val = sub_sheds_id_array == value
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        np.putmask(new_data_array, set_mask_val, geom.GetArea())
        
        feat.Destroy()
        
    band_area.WriteArray(new_data_array, 0, 0)  
    return raster_area

def create_mean_raster(raster, path, sub_sheds, field_name, shed_mask):
    """
    """
    raster_mean = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    band_mean = raster_mean.GetRasterBand(1)
    pixel_data_array = band_mean.ReadAsArray()
    nodata = band_mean.GetNoDataValue()
    band_mean.Fill(nodata)
    sub_sheds_id_array = np.copy(shed_mask)
    new_data_array = np.copy(pixel_data_array)
    
    for feat in sub_sheds.GetLayer(0):
        index = feat.GetFieldIndex(field_name)
        value = feat.GetFieldAsInteger(index)
        mask_val = sub_sheds_id_array != value
        set_mask_val = sub_sheds_id_array == value
        masked_array = np.ma.array(pixel_data_array, mask = mask_val)
        comp_array = np.ma.compressed(masked_array)
        mean = sum(comp_array) / len(comp_array)
        np.putmask(new_data_array, set_mask_val, mean)
        
        feat.Destroy()
        
    band_mean.WriteArray(new_data_array, 0, 0)  
    return raster_mean

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
    
def create_etk_root_rasters(key_raster, new_path, nodata, bio_dict, field):
    """
    """
    #brute force create raster from table values
    tmp_raster = \
        invest_cython_core.newRasterFromBase(key_raster, new_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
    key_band = key_raster.GetRasterBand(1)
    key_nodata = key_band.GetNoDataValue()
    array = key_band.ReadAsArray()
    #http://stackoverflow.com/questions/3403973/fast-replacement-of-values-in-a-numpy-array
    new_array = array.astype(np.float)
    for k, v in bio_dict.iteritems(): 
        new_array[array==int(k)] = float(v[field])
        if k=='57':
            LOGGER.debug('new_array : %s : %s', k, v)
    tmp_band = tmp_raster.GetRasterBand(1)
    tmp_band.WriteArray(new_array, 0, 0)
    return tmp_raster

def water_scarcity(args):
    """
    """
    #water yield functionality goes here    
    LOGGER.info('Starting Water Scarcity Calculation')
        
def valuation(args):
    """
    """
    #water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')