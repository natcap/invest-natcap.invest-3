"""InVEST Biodiversity model core function  module"""

from invest_natcap import raster_utils

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
        #Fill raster to all 1's (fully accessible) incase polygons do not cover
        #land area
        access_base.GetRasterBand(1).Fill(1)
        access_raster = make_raster_from_shape(access_base, access_shape, 'ACCESS')
    except KeyError:
        LOGGER.debug('No Access Shape Provided')
        access_shape = None

    #def tracer_op(
    # 1) Blur all threats with gaussian filter
    for threat, threat_data in args['threat_dict'].iteritems():
        threat_raster = args['density_dict'][threat]
        if threat_raster is None:
            LOGGER.warn('No threat raster found for threat : %s',  threat)
            LOGGER.warn('Continuing run without factoring in threat')
            break
        threat_band = threat_raster.GetRasterBand(1)
        threat_nodata = threat_band.GetNoDataValue()

        filtered_raster = \
            raster_utils.new_raster_from_base(threat_raster, str(intermediate_dir +
                    threat+'filtered.tif'),'GTiff',
                    -1.0, gdal.GDT_Float32)
        # get the mean cell size
        mean_cell_size = (abs(lulc_prop['width']) + abs(lulc_prop['height'])) / 2.0
        sigma = 2.99 / mean_cell_size

        filtered_out_matrix = \
            clip_and_op(threat_raster.GetRasterBand(1).ReadAsArray(), sigma, \
                        ndimage.gaussian_filter, matrix_type=float, 
                        in_matrix_nodata=float(threat_raster.GetRasterBand(1).GetNoDataValue()),
                        out_matrix_nodata=-1.0)
        filtered_band = filtered_raster.GetRasterBand(1)
        filtered_band.WriteArray(filtered_out_matrix)
        filtered_band = None
        filtered_raster.FlushCache()
    # 2) Apply threats on land cover

#   #Process density layers / each threat

#   #For all threats:
#   for threat, threat_data in args['threat_dict'].iteritems():
#       #get weight, name, max_idst, decay
#       #mulitply max_dist by 1000 (must be a conversion to meters)
#       #get proper density raster, depending on land cover
#       
#       #Adjust threat by distance:
#           #Calculate neighborhood

#       #Adjust threat by weight:
#       weight_multiplier = float(threat_data['WEIGHT']) / weight_sum
#       def adjust_weight(dist):
#           return dist * weight_multiplier 
#       raster_utils.vectorize1ArgOp(dist.GetRasterBand(1), adjust_weight, weight_out)

#       #Adjust threat by protection / access
#       if access_shape != None:
#           def adjust_access(weight, access):
#               return weight * access
#           raster_utils.vectorize2ArgOp(weight_band, access_band, adjust_access, access_out)

#       #Adjust threat by sensitivity
#      sens_uri = intermediate_dir + 'sens_'+threat+'.tif'
#      sensitivity_raster = make_raster_from_lulc(args['landuse'], sens_uri)
#      sensitivity_raster = raster_from_table_values(args['landuse'], sensitivity_raster, 
#                                                    args['sensitivity_dict'], 'L_'+threat)        
#      def adjust_sens(sens, acc):
#          return sens * acc

##I can probably just do a giant vectorize_raster call on these 4 rasters and do the calculation at once        

#   #Compute Degradation of all threats
#       #Some all the final threat rasters from above. Prob store them in a list.
#   def degredation_op(*raster):
#       return sum(raster)
#   degredation_raster = raster_utils.vectorize_rasters(threat_raster_list, degredation_op, nodata=-1.0)
#   #Compute quality for all threats
#   z = 2.5
#   ksq = k**z
#   def quality_op(degradation,habitat):
#       returnhabitat * (1 - ((degredation**z) / (degredation**z + ksq)))
#   quality_raster = raster_utils.vectorize_rasters([degredation_raster, habitat], quality_op)


    #Adjust quality by habitat status

    #Comput Rarity if user supplied baseline raster


    LOGGER.debug('Finished biodiversity biophysical calculations')

def clip_and_op(in_matrix, arg1, op, matrix_type=float, in_matrix_nodata=-1, out_matrix_nodata=-1, kwargs={}):
    """Apply an operatoin to a matrix after the matrix is adjusted for nodata
        values. After the operation is complete, the matrix will have pixels
        culled based on the input matrix's original values that were less than 0
        (which assumes a nodata value of below zero).

        in_matrix - a numpy matrix for use as the first argument to op
        arg1 - an argument of whatever type is necessary for the second argument
            of op
        op - a python callable object with two arguments: in_matrix and arg1
        in_matrix_nodata - a python int or float
        out_matrix_nodata - a python int or float
        kwargs={} - a python dictionary of keyword arguments to be passed in to
            op when it is called.

        returns a numpy matrix."""

    # Making a copy of the in_matrix so as to avoid side effects from putmask
    matrix = in_matrix.astype(matrix_type)

    # Convert nodata values to 0
    np.putmask(matrix, matrix == in_matrix_nodata, 0)

    # Apply the operation specified by the user
    filtered_matrix = op(matrix, arg1, **kwargs)

    # Restore nodata values to their proper places.
    np.putmask(filtered_matrix, in_matrix== in_matrix_nodata, out_matrix_nodata)

    return filtered_matrix

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

    #out_band = out_raster.GetRasterBand(1)
    out_raster = raster_utils.vectorize_rasters([key_raster], vop, nodata=-1.0)

    return out_raster

def make_raster_from_lulc(lulc_dataset, raster_uri):
    LOGGER.debug('Creating new raster from LULC: %s', raster_uri)
    dataset = \
        raster_utils.new_raster_from_base(lulc_dataset, raster_uri, 'GTiff', \
                                          -1, gdal.GDT_Float32)
    return dataset


