"""InVEST Biodiversity model core function  module"""
import math
import os.path
import logging

from osgeo import gdal
from osgeo import ogr
import numpy as np
import scipy.ndimage as ndimage

from invest_natcap import raster_utils
LOGGER = logging.getLogger('biodiversity_core')

def biophysical(args):
    """Execute the biophysical component of the biodiversity model.

       args - a python dictionary with at least the following components:
       args['workspace_dir'] - a uri to the directory that will write output
       args['landuse_dict'] - a python dictionary with keys depicting the
           landuse scenario (current, future, or baseline) and the values GDAL
           datasets.
           {'_c':current dataset, '_f':future dataset, '_b':baseline dataset}
       args['threat_dict'] - a python dictionary representing the threats table
            {'crp':{'THREAT':'crp','MAX_DIST':'8.0','WEIGHT':'0.7','DECAY':'0'},
             'urb':{'THREAT':'urb','MAX_DIST':'5.0','WEIGHT':'0.3','DECAY':'0'},
             ... }
       args['sensitivity_dict'] - a python dictionary representing the sensitivity table
            {'1':{'LULC':'1','NAME':'Residential','HABITAT':'1','L_crp':'0.4','L_urb':'0.45'...},
             '11':{'LULC':'11','NAME':'Urban','HABITAT':'1','L_crp':'0.6','L_urb':'0.3'...},
             ...}
       args['density_dict'] - a python dictionary that stores any density
           rasters (threat rasters) corresponding to the entries in the threat
           table and whether the density raster belongs to the current, future,
           or baseline raster. Example:
           {'dens_c': {'crp_c' : crp_c.tif, 'srds_c' : srds_c.tif, ...},
            'dens_f': {'crp_f' : crp_f.tif, 'srds_f' : srds_f.tif, ...},
            'dens_b': {'crp_b' : crp_b.tif, 'srds_b' : srds_b.tif, ...}
           }
       args['access_shape'] - an OGR datasource of polygons depicting any protected/reserved
           land boundaries
       args['half_saturation'] - an integer that determines the spread and
           central tendency of habitat quality scores
       args['result_suffix'] - a string of the desired suffix

       returns nothing."""

    LOGGER.debug('Starting biodiversity biophysical calculations')

    output_dir = os.path.join(args['workspace_dir'], 'output')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    cur_landuse = args['landuse_dict']['_c']
    threat_dict = args['threat_dict']
    sensitivity_dict = args['sensitivity_dict']
    half_saturation = args['half_saturation']
    
    out_nodata = -1.0
    
    #Create raster of habitat based on habitat field
    habitat_uri = os.path.join(intermediate_dir, 'habitat.tif')
    
    habitat_raster = \
        raster_from_dict(cur_landuse, habitat_uri, sensitivity_dict,\
                         'HABITAT', out_nodata, False)
    
    # If access_lyr: convert to raster, if value is null set to 1, 
    # else set to value
    try:
        access_shape = args['access_shape']
        LOGGER.debug('Handling Access Shape')
        access_uri = os.path.join(intermediate_dir, 'access_layer.tif')
        access_base = make_raster_from_lulc(cur_landuse, access_uri)
        #Fill raster to all 1's (fully accessible) incase polygons do not cover
        #land area
        access_base.GetRasterBand(1).Fill(1)
        access_raster = make_raster_from_shape(access_base, access_shape, 'ACCESS')
    except KeyError:
        LOGGER.debug('No Access Shape Provided')
        access_shape = None
        access_raster = None

    # calculate the weight sum which is the sum of all the threats weights
    weight_sum = 0.0
    for threat_data in threat_dict.itervalues():
        #Sum weight of threats
        weight_sum = weight_sum + float(threat_data['WEIGHT'])
    
    LOGGER.debug('landuse_dict : %s', args['landuse_dict']) 

    # for each land cover raster provided compute habitat quality
    for lulc_key, lulc_ras in args['landuse_dict'].iteritems():
        try:
            LOGGER.debug('Calculating results for landuse : %s', lulc_key)
            # get raster properties: cellsize, width, height, 
            # cells = width * height, extent    
            lulc_prop = get_raster_properties(cur_landuse)

            # initialize a list that will store all the density/threat rasters
            # after they have been adjusted for distance, weight, and access
            degradation_rasters = []
            
            # intitialize a list to store raster nodata values that correspond
            # to the rasters stored in 'degradation_rasters' above
            deg_adjusted_nodata_list = []
            
            # variable to indicate whether we should break out of calculations
            # for a land cover because a threat raster was not found
            exit_landcover = False

            # adjust each density/threat raster for distance, weight, and access 
            for threat, threat_data in threat_dict.iteritems():

                LOGGER.debug('Calculating threat : %s', threat)
                LOGGER.debug('Threat Data : %s', threat_data)
           
                # get the density raster for the specific threat
                threat_raster = args['density_dict']['density'+lulc_key][threat]
            
                # if threat / density raster is not found for a landcover, that
                # landcover should be skipped
                if threat_raster is None:
                    LOGGER.warn('No threat raster found for threat : %s',
                                threat+lulc_key)
                    LOGGER.warn('Moving to next landcover')
                    exit_landcover = True
                    break 

                threat_band = threat_raster.GetRasterBand(1)
                threat_nodata = float(threat_band.GetNoDataValue())
                filtered_threat_uri = \
                    os.path.join(intermediate_dir, str(threat+'_filtered.tif'))
                
                # create a new raster to output distance adjustments to
                filtered_raster = \
                    raster_utils.new_raster_from_base(threat_raster, filtered_threat_uri, 
                                                      'GTiff', out_nodata, gdal.GDT_Float32)
                # get the mean cell size, using absolute value because we could
                # get a negative for height or width
                mean_cell_size = (abs(lulc_prop['width']) + abs(lulc_prop['height'])) / 2.0
                
                # convert max distance (given in KM) to meters
                dr_max = float(threat_data['MAX_DIST']) * 1000.0
                
                # convert max distance from meters to the number of pixels that
                # represents on the raster
                dr_pixel = dr_max / mean_cell_size
                
                # compute sigma to be used in a gaussian filter.  Sigma is
                # derived from using equation 12.2 in users manual and the
                # gaussian equation. 2.99573 is from users guide and old code
                sigma = \
                    math.sqrt(dr_pixel / (2.99573 * 2.0))
                LOGGER.debug('Sigma for gaussian : %s', sigma)

                # use a gaussian_filter to compute the effect that a threat has over a
                # distance, on a given pixel. 
                filtered_out_matrix = \
                    clip_and_op(threat_band.ReadAsArray(), sigma,\
                                ndimage.gaussian_filter, matrix_type=float,\
                                in_matrix_nodata=threat_nodata,
                                out_matrix_nodata=out_nodata)
                
                filtered_band = filtered_raster.GetRasterBand(1)
                filtered_band.WriteArray(filtered_out_matrix)
                filtered_raster.FlushCache()

                # create sensitivity raster based on threat
                sens_uri = \
                    os.path.join(intermediate_dir, str('sens_'+threat+lulc_key+'.tif'))
                
                sensitivity_raster = \
                    raster_from_dict(lulc_ras, sens_uri,\
                        sensitivity_dict, 'L_'+threat, -1.0, True,\
                        error_message='A lulc type in the land cover was not\
                        found in the sensitivity table. The erroring pixel\
                        value was : ')        
                sensitivity_raster.FlushCache()
               
                weight_avg = float(threat_data['WEIGHT']) / weight_sum

                def partial_degradation(*rasters):
                    """For a given threat return the weighted average of the product of
                        the threats sensitivity, the threats access, and the threat 
                        adjusted by distance
                        
                        *rasters - a list of floats

                        returns - the degradation for this threat
                        """
                    # there is a nodata value if this list is not empty
                    if len(filter(lambda (x,y): x==y, \
                               zip(rasters, adjusted_nodata_list))) == 0:
                        return np.prod(rasters) * weight_avg
                    return out_nodata
                
                # build lists of the two rasters and their respective nodata
                # values to be used to calculate their individual degradation
                # raster
                adjusted_list = [filtered_raster, sensitivity_raster]
                adjusted_nodata_list =\
                    [filtered_raster.GetRasterBand(1).GetNoDataValue(),
                     sensitivity_raster.GetRasterBand(1).GetNoDataValue()]
                
                # set the adjusted raster lists depending on whether the 
                # access shapefile was provided
                if access_raster is not None:
                    adjusted_list.append(access_raster)
                    access_band = access_raster.GetRasterBand(1)
                    adjusted_nodata_list.append(access_band.GetNoDataValue())
                
                deg_uri = \
                    os.path.join(intermediate_dir,
                                 str('deg_'+threat+lulc_key+'.tif'))
                deg_ras =\
                    raster_utils.vectorize_rasters(adjusted_list, \
                        partial_degradation, raster_out_uri=deg_uri,\
                        nodata=out_nodata)
                
                degradation_rasters.append(deg_ras)
                deg_adjusted_nodata_list.append(deg_ras.GetRasterBand(1).GetNoDataValue())
            
            # check to see if we got here because a threat raster was missing
            # and if so then we want to skip to the next landcover
            if exit_landcover:
                continue

            def sum_degradation(*rasters):
                """A vectorized function that sums all the degradation
                    rasters created above.

                    *rasters - a list of floats where each float is a
                        degradation score from a pixel from one of the
                        threat rasters.

                    returns - the total degradation score for the pixel
                """
                # there is a nodata value if this list is not empty
                if len(filter(lambda (x,y): x==y, zip(rasters,
                    deg_adjusted_nodata_list))) == 0:
                    return np.sum(rasters)
                return out_nodata
            
            deg_sum_uri = \
                os.path.join(output_dir, 'deg_sum_out'+lulc_key+'.tif')
            
            sum_deg_raster = \
                raster_utils.vectorize_rasters(degradation_rasters, sum_degradation,\
                                               raster_out_uri=deg_sum_uri,
                                               nodata=out_nodata)

            #Compute habitat quality
            # z is a scaling parameter set to 2.5 as noted in the users
            # guide
            z = 2.5
            
            # a term used below to compute habitat quality
            ksq = half_saturation**z
            
            sum_deg_nodata =\
                sum_deg_raster.GetRasterBand(1).GetNoDataValue()
            
            habitat_nodata =\
                habitat_raster.GetRasterBand(1).GetNoDataValue()
            
            def quality_op(degradation, habitat):
                """Vectorized function that computes habitat quality given
                    a degradation and habitat value.

                    degradation - a float from the created degradation
                        raster above. 
                    habitat - a float indicating habitat suitability from
                        from the habitat raster created above.

                    returns - a float representing the habitat quality
                        score for a pixel
                """
                # there is a nodata value if this list is not empty
                if degradation == sum_deg_nodata or \
                        habitat == habitat_nodata:
                    return out_nodata

                return habitat * (1 - ((degradation**z) / (degradation**z + ksq)))
            
            quality_uri = \
                os.path.join(output_dir, 'quality_out'+lulc_key+'.tif')
            
            quality_raster = \
                raster_utils.vectorize_rasters([sum_deg_raster, habitat_raster], 
                                               quality_op, raster_out_uri=quality_uri,
                                               nodata=out_nodata)
        except:
            LOGGER.error('An error was encountered processing landuse%s', lulc_key)
            LOGGER.debug('Attempting to move on to next landuse map')
            continue 
    
    #Compute Rarity if user supplied baseline raster
    try:    
        # will throw a KeyError exception if no base raster is provided
        lulc_base = args['landuse_dict']['_b']
        
        # get the area of a base pixel to use for computing rarity where the 
        # pixel sizes are different between base and cur/fut rasters
        base_properties = get_raster_properties(lulc_base)
        base_area = base_properties['width'] * base_properties['height']

        base_nodata = lulc_base.GetRasterBand(1).GetNoDataValue()
        rarity_nodata = float(np.finfo(np.float32).min)
        
        lulc_code_count_b = raster_pixel_count(lulc_base)
        
        # compute rarity for current landscape and future (if provided)
        for lulc_cover in ['_c', '_f']:
            try:
                lulc_x = args['landuse_dict'][lulc_cover]
                
                # get the area of a cur/fut pixel
                lulc_properties = get_raster_properties(lulc_x)
                lulc_area = lulc_properties['width'] * lulc_properties['height']
                
                lulc_nodata = lulc_x.GetRasterBand(1).GetNoDataValue()
                
                LOGGER.debug('Base and Cover NODATA : %s : %s', base_nodata,
                        lulc_nodata) 
                
                def trim_op(base, cover_x):
                    """Vectorized function used in vectorized_rasters. Trim
                        cover_x to the mask of base
                        
                        base - the base raster from 'lulc_base' above
                        cover_x - either the future or current land cover raster
                            from 'lulc_x' above
                        
                        return - out_nodata if base or cover_x is equal to their
                            nodata values or the cover_x value
                        """
                    if base==base_nodata or cover_x==lulc_nodata:
                        return out_nodata
                    return float(cover_x) 
                
                LOGGER.debug('Create new cover for %s', lulc_cover)
                new_cover_uri = \
                    os.path.join(intermediate_dir, 'new_cover'+lulc_cover+'.tif')
                
                # set the current/future land cover to be masked to the base
                # land cover
                new_cover = \
                    raster_utils.vectorize_rasters([lulc_base, lulc_x], trim_op,
                            raster_out_uri=new_cover_uri,
                            datatype=gdal.GDT_Int32, nodata=out_nodata)
                
                lulc_code_count_x = raster_pixel_count(new_cover)
                
                # a dictionary to map LULC types to a number that depicts how
                # rare they are considered                
                code_index = {}
                
                # compute the ratio or rarity index for each lulc code where we
                # return 0.0 if an lulc code is found in the cur/fut land cover
                # but not the baseline
                for code in lulc_code_count_x.iterkeys():
                    try:
                        numerator = float(lulc_code_count_x[code] * lulc_area)
                        denominator = float(lulc_code_count_b[code] * base_area)
                        ratio = 1.0 - (numerator / denominator)
                        code_index[code] = ratio
                    except KeyError:
                        code_index[code] = 0.0
                
                def map_ratio(cover):
                    """Vectorized operation used to map a dictionary to a lulc raster
                    
                    cover - refers to the 'new_cover' raster generated above
                    
                    return - rarity_nodata if code is not in the dictionary,
                        otherwise return the rarity index pertaining to that
                        code"""
                    if cover in code_index:
                        return code_index[cover]
                    return rarity_nodata
                
                rarity_uri = \
                    os.path.join(output_dir, 'rarity'+lulc_cover+'.tif')

                rarity = \
                    raster_utils.vectorize_rasters([new_cover], map_ratio,\
                        raster_out_uri=rarity_uri, nodata=rarity_nodata)
                
                rarity = None
            
            except KeyError:
                continue
    
    except KeyError:
        LOGGER.info('Baseline not provided to compute Rarity')

    LOGGER.debug('Finished biodiversity biophysical calculations')

def raster_pixel_count(ds):
    """Determine how many of each unique pixel lies in the datasoure (ds)
    
        ds - a GDAL raster dataset

        returns -  a dictionary whose keys are the unique pixel values and whose
                   values are the number of occurrences
    """

    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    counts = {}
    for row_index in range(band.YSize):
        cur_array = band.ReadAsArray(0, row_index, band.XSize, 1)
        for val in np.unique(cur_array):
            if val == nodata:
                continue
            if val in counts:
                counts[val] = \
                    float(counts[val] + cur_array[cur_array==val].size)
            else:
                counts[val] = float(cur_array[cur_array==val].size)

    return counts


def clip_and_op(in_matrix, arg1, op, matrix_type=float, in_matrix_nodata=-1, 
                out_matrix_nodata=-1, kwargs={}):
    """Apply an operatoin to a matrix after the matrix is adjusted for nodata
        values. After the operation is complete, the matrix will have pixels
        culled based on the input matrix's original values that were less than 0
        (which assumes a nodata value of below zero).

        in_matrix - a numpy matrix for use as the first argument to op
        arg1 - an argument of whatever type is necessary for the second argument
            of op
        op - a python callable object with two arguments: in_matrix and arg1
        matrix_type - a python type, default is float
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
    """Burn an attribute value from a polygon shapefile onto an
       existing blank raster

       base_raster - a gdal raster dataset to burn the shapefile
                     values onto
       shape - a ORG datasource polygon shapefile
       attr - a python string of the attribute field to burn values
              from

       returns - a GDAL raster dataset"""
    
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
    dataset_dict['width'] = float(gt[1])
    dataset_dict['height'] = float(gt[5])
    dataset_dict['x_size'] = dataset.GetRasterBand(1).XSize    
    dataset_dict['y_size'] = dataset.GetRasterBand(1).YSize    
    LOGGER.debug('Raster_Properties : %s', dataset_dict)
    return dataset_dict

def raster_from_dict(key_raster, out_uri, attr_dict, field, out_nodata,\
        raise_error, error_message='An Error occured mapping a dictionary to a\
        raster'):
    """Creates a new raster from 'key_raster' where the pixel values from
       'key_raster' are the keys to a dictionary 'attr_dict'. The values 
       corresponding to those keys is what is written to the new raster. If a
       value from 'key_raster' does not appear as a key in 'attr_dict' then
       raise an Exception if 'raise_error' is True, otherwise return a
       'out_nodata'
    
       key_raster - a GDAL raster dataset whose pixel values relate to the 
                     keys in 'attr_dict'
       out_uri - a string for the output path of the created raster
       attr_dict - a dictionary representing a table of values we are interested
                   in making into a raster                  
       field - a string of which field in the table or key in the dictionary 
               to use as the new raster pixel values
       out_nodata - a floating point value that is the nodata value.
       raise_error - a boolean that decides how to handle the case where the
           value from 'key_raster' is not found in 'attr_dict'. If 'raise_error'
           is True, raise Exception, if False, return 'out_nodata'
       error_message - a string that is printed out with the raised Exception if
           'raise_error' is set to True

       returns - a GDAL raster, or raises an Exception and fail if:
           1) raise_error is True and
           2) the value from 'key_raster' is not a key in 'attr_dict'
    """

    LOGGER.debug('Starting raster_from_dict')
    
    #Add the nodata value as a field to the dictionary so that the vectorized
    #operation can just look it up instead of having an if,else statement
    attr_dict[out_nodata] = {field:float(out_nodata)}

    if raise_error:
        def vop(key):
            """Operation passed to numpy function vectorize that uses 'key' as the 
                key to the local dictionary 'attr_dict'. Returns the value in place
                of the key for the new raster
               
                key - a float or int or string from the local raster 
                    'key_raster' that is used to look up a value in the 
                    dictionary 'attr_dict'

               returns - the 'field' value corresponding to the 'key' or raises
                   an Exception if 'key' is not found as a key in 'attr_dict'
            """
            if str(key) in attr_dict:
                return attr_dict[str(key)][field]
            else:
                raise KeyError(error_message)
    else:
        def vop(key):
            """Operation passed to numpy function vectorize that uses 'key' as the 
                key to the local dictionary 'attr_dict'. Returns the value in place
                of the key for the new raster
               
                key - a float or int or string from the local raster 
                    'key_raster' that is used to look up a value in the 
                    dictionary 'attr_dict'

               returns - the 'field' value corresponding to the 'key' or
                   'out_nodata' if 'key' is not a key in 'attr_dict'
            """
            if str(key) in attr_dict:
                return attr_dict[str(key)][field]
            else:
                return out_nodata

    out_raster = raster_utils.vectorize_rasters([key_raster], vop,
            raster_out_uri=out_uri, nodata=out_nodata)

    return out_raster

def make_raster_from_lulc(lulc_dataset, raster_uri):
    """Create a new raster from the lulc
    """
    LOGGER.debug('Creating new raster from LULC: %s', raster_uri)
    dataset = \
        raster_utils.new_raster_from_base(lulc_dataset, raster_uri, 'GTiff', \
                                          -1, gdal.GDT_Float32)
    return dataset


