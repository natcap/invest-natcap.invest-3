"""InVEST Biodiversity model core function  module"""

import invest_cython_core
from invest_natcap.invest_core import invest_core

from osgeo import gdal
from osgeo import ogr
import numpy as np
import scipy.ndimage as ndimage

import os.path
import logging

LOGGER = logging.getLogger('biodiversity_core')


def biophysical(args):
    """Execute the biophysical component of the pollination model.

       args - a python dictionary with at least the following components:
       args['workspace_dir'] - a uri to the directory that will write output
       args['landuse'] - a Gdal dataset
       args['threat_dict'] - a python dictionary representing the threats table
       args['sensitivity_dict'] - a python dictionary representing the sensitivity table
       args['density_dict'] - a python dictionary that stores one or more gdal datasets
                              based on the number of threats given in the threat table
       args['access_shape'] - a ogr polygon shapefile depicting any protected/reserved
                              land boundaries
       args['half_saturation'] - an integer
       args['result_suffix'] - a string


        returns nothing."""

    LOGGER.debug('Starting biodiversity biophysical calculations')
    output_dir = args['workspace_dir'] + os.sep + 'output/'
    intermediate_dir = args['workspace_dir'] + os.sep + 'intermediate/'
    threat_dict = args['threat_dict']
    #Get raster properties: cellsize, width, height, cells = width * height, extent    
    lulc_prop = get_raster_properties(args['landuse'])
    #Create raster of habitat based on habitat field
    habitat_uri = intermediate_dir + 'habitat.tif'
    habitat_raster = make_raster_from_lulc(args['landuse'], habitat_uri)
    habitat_raster = raster_from_table_values(args['landuse'], habitat_raster, args['sensitivity_dict'], 'HABITAT')

    #Sum weight of threats
    weight_sum = 0.0
    for threat_info in threat_dict.itervalues():
        weight_sum = weight_sum + float(threat_info['WEIGHT'])

    
    #Check that threat count matches with sensitivity
        #Will be doing this in validation (hopefully...) or at the uri level

    #If access_lyr: convert to raster, if value is null set to 1, else set to value
    try:
        access_shape = args['access_shape']
        LOGGER.debug('Handling Access Shape')
        access_uri = intermediate_dir + 'access_layer.tif'
        access_base = make_raster_from_lulc(args['landuse'], access_uri)
        access_raster = make_raster_from_shape(access_base, access_shape, 'ACCESS')
    except:
        LOGGER.debug('No Access Shape Provided')
        access_shape = None

    #Process density layers / each threat

    #For all threats:
        #get weight, name, max_idst, decay
        #mulitply max_dist by 1000 (must be a conversion to meters
        #get proper density raster, depending on land cover
        
        #Adjust threat by distance:
            #Calculate neighborhood

        #Adjust threat by weight:
        
        #Adjust threat by protection / access

        #Adjust threat by sensitivity

    #Compute Degradation of all threats

    #Compute quality for all threats

    #Adjust quality by habitat status

    #Comput Rarity if user supplied baseline raster


    LOGGER.debug('Finished biodiversity biophysical calculations')

def make_raster_from_shape(base_raster, shape, attr):
    """Burn an attribute value from a polygone shapefile onto an
       existing blank raster

       base_raster - a gdal raster dataset to burn the shapefile
                     values onto
       shape - a ogr polygon shapefile
       attr - a python string of the attribute field to burn values
              from

       returns - a gdal raster"""
    
    attribute_string = 'ATTRIBUTE=' + attr
    gdal.RasterizeLayer(base_raster, [1], shape.GetLayer(0),
                        options = [attribute_string])

    return base_raster 
       
def get_raster_properties(dataset):
    """Get the width, height, cover, extent of the raster

       dataset - a raster dataset
        
      returns - a dictionary with the properties stored under relevant keys
    """
    dataset_dict = {}
    gt = dataset.GetGeoTransform()
    dataset_dict['width'] = gt[1]
    dataset_dict['height'] = gt[5]
    dataset_dict['x_size'] = dataset.GetRasterBand(1).XSize    
    dataset_dict['y_size'] = dataset.GetRasterBand(1).YSize    
    dataset_dict['mask'] = dataset.GetRasterBand(1).GetMaskBand()
    LOGGER.debug('Raster_Properties : %s', dataset_dict)
    return dataset_dict

def raster_from_table_values(key_raster, out_raster, attr_dict, field):
    """Creates a new raster from 'key_raster' whose values are data from a 
       dictionary that directly relates to the pixel value from 'key_raster'
    
       key_raster - a GDAL raster dataset whose pixel values relate to the 
                     keys in 'attr_dict'
       out_raster - a Gdal raster dataset to write out to
       attr_dict - a dictionary representing a table of values we are interested
                   in making into a raster                  
       field - a string of which field in the table or key in the dictionary 
               to use as the new raster pixel values
       
       returns - a GDAL raster
    """

    LOGGER.debug('Starting raster_from_table_values')
    key_band = key_raster.GetRasterBand(1)
    out_nodata = out_raster.GetRasterBand(1).GetNoDataValue()
    LOGGER.debug('raster_from_table_values.out_nodata : %s', out_nodata)
    #Add the nodata value as a field to the dictionary so that the vectorized
    #operation can just look it up instead of having an if,else statement
    attr_dict[out_nodata] = {field:float(out_nodata)}

    def vop(lulc):
        """Operation returns the 'field' value that directly corresponds to
           it's lulc type
           
           lulc - a numpy array with the lulc type values as integers
        
           returns - the 'field' value corresponding to the lulc type
        """
        if str(lulc) in attr_dict:
            return attr_dict[str(lulc)][field]
        else:
            return out_nodata

    out_band = out_raster.GetRasterBand(1)
    invest_core.vectorize1ArgOp(key_band, vop, out_band)

    return out_raster

def make_raster_from_lulc(lulc_dataset, raster_uri):
    LOGGER.debug('Creating new raster from LULC: %s', raster_uri)
    dataset = invest_cython_core.newRasterFromBase(\
        lulc_dataset, raster_uri, 'GTiff', -1, gdal.GDT_Float32)
    return dataset


