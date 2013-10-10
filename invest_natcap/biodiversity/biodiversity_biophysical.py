"""InVEST Habitat Quality model"""
import math
import os.path
import logging
import csv

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import numpy as np
import scipy.ndimage as ndimage

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('habitat_quality')

def execute(args):
    """Open files necessary for the portion of the habitat_quality
        model.

        args - a python dictionary with at least the following components:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation (required)
        args['landuse_cur_uri'] - a uri to an input land use/land cover raster
            (required)
        args['landuse_bas_uri'] - a uri to an input land use/land cover raster
            (optional, but required for rarity calculations)
        args['landuse_fut_uri'] - a uri to an input land use/land cover raster
            (optional)
        args['threats_uri'] - a uri to an input CSV containing data
            of all the considered threats. Each row is a degradation source
            and each column a different attribute of the source with the
            following names: 'THREAT','MAX_DIST','WEIGHT' (required).
        args['access_uri'] - a uri to an input polygon shapefile containing
            data on the relative protection against threats (optional)
        args['sensitivity_uri'] - a uri to an input CSV file of LULC types,
            whether they are considered habitat, and their sensitivity to each
            threat (required)
        args['half_saturation_constant'] - a python float that determines
            the spread and central tendency of habitat quality scores 
            (required)
        args['suffix'] - a python string that will be inserted into all
            raster uri paths just before the file extension.

        returns nothing."""

    workspace = args['workspace_dir']
    
    # create dictionary to hold values that will be passed to the core
    # functionality
    biophysical_args = {}
    biophysical_args['workspace_dir'] = workspace

    # if the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = '_' + args['suffix']
    except:
        suffix = ''

    biophysical_args['suffix'] = suffix

    # Check to see if each of the workspace folders exists.  If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([inter_dir, out_dir])

    # if the input directory is not present in the workspace then throw an
    # exception because the threat rasters can't be located.
    input_dir_low = os.path.join(workspace, 'input')
    input_dir_up = os.path.join(workspace, 'Input')
    input_dir = None

    for input_dir_case in [input_dir_low, input_dir_up]:
        if os.path.isdir(input_dir_case):
            input_dir = input_dir_case
            break
    
    if input_dir is None:
        raise Exception('The input directory where the threat rasters ' + \
                        'should be located cannot be found.')
    
    biophysical_args['threat_dict'] = \
        make_dictionary_from_csv(args['threats_uri'],'THREAT')

    biophysical_args['sensitivity_dict'] = \
        make_dictionary_from_csv(args['sensitivity_uri'],'LULC')

    # check that the threat names in the threats table match with the threats
    # columns in the sensitivity table. Raise exception if they don't.
    if not threat_names_match(biophysical_args['threat_dict'], \
            biophysical_args['sensitivity_dict'], 'L_'):
        raise Exception('The threat names in the threat table do ' + \
            'not match the columns in the sensitivity table')

    biophysical_args['half_saturation'] = \
           float(args['half_saturation_constant'])    

    # if the access shapefile was provided add it to the dictionary
    try:
        biophysical_args['access_shape'] = ogr.Open(args['access_uri'])
    except KeyError:
        pass

    # Determine which land cover scenarios we should run, and append the
    # appropriate suffix to the landuser_scenarios list as necessary for the
    # scenario.
    landuse_scenarios = {'cur':'_c'}
    scenario_constants = [('landuse_fut_uri', 'fut', '_f'), \
                          ('landuse_bas_uri', 'bas', '_b')]
    for lu_uri, lu_time, lu_ext in scenario_constants:
        if lu_uri in args:
            landuse_scenarios[lu_time] = lu_ext

    # declare dictionaries to store the land cover rasters and the density
    # rasters pertaining to the different threats
    landuse_dict = {}
    density_dict = {}

    # for each possible land cover that was provided try opening the raster and
    # adding it to the dictionary. Also compile all the threat/density rasters
    # associated with the land cover
    for scenario, ext in landuse_scenarios.iteritems():
        landuse_dict[ext] = \
            gdal.Open(args['landuse_' + scenario + '_uri'], gdal.GA_ReadOnly)
        
        # add a key to the density dictionary that associates all density/threat
        # rasters with this land cover
        density_dict['density' + ext] = {}

        # for each threat given in the CSV file try opening the associated
        # raster which should be found in workspace/input/
        for threat in biophysical_args['threat_dict']:
            try:
                if ext == '_b':
                    density_dict['density' + ext][threat] = open_ambiguous_raster(
                            os.path.join(input_dir, threat + ext),
                            raise_error=False)
                else:
                    density_dict['density' + ext][threat] = open_ambiguous_raster(
                            os.path.join(input_dir, threat + ext))
            except:
                raise Exception('Error: Failed to open raster for the '
                    'following threat : %s . Please make sure the threat names '
                    'in the CSV table correspond to threat rasters in the input '
                    'folder.' % os.path.join(input_dir, threat + ext))
    
    biophysical_args['landuse_dict'] = landuse_dict
    biophysical_args['density_dict'] = density_dict

    # checking to make sure the land covers have the same projections and are
    # projected in meters. We pass in 1.0 because that is the unit for meters
    if not check_projections(landuse_dict, 1.0):
        raise Exception('Land cover projections are not the same or are' +\
                        'not projected in meters')

    biophysical(biophysical_args)

def open_ambiguous_raster(uri, raise_error=True):
    """Open and return a gdal dataset given a uri path that includes the file
        name but not neccessarily the suffix or extension of how the raster may
        be represented.

        uri - a python string of the file path that includes the name of the
              file but not its extension

        raise_error - a Boolean that indicates whether the function should
            raise an error if a raster file could not be opened. 

        return - a gdal dataset or NONE if no file is found with the pre-defined
                 suffixes and 'uri'"""
    # Turning on exceptions so that if an error occurs when trying to open a
    # file path we can catch it and handle it properly
    gdal.UseExceptions()
    
    # a list of possible suffixes for raster datasets. We currently can handle
    # .tif and directory paths
    possible_suffixes = ['', '.tif', '.img']
    
    # initialize dataset to None in the case that all paths do not exist
    dataset = None
    for suffix in possible_suffixes:
        full_uri = uri + suffix
        if not os.path.exists(full_uri):
            continue
        try:
            dataset = gdal.Open(full_uri, gdal.GA_ReadOnly)
        except:
            dataset = None            
        
        # return as soon as a valid gdal dataset is found
        if dataset is not None:
            break

    # Turning off exceptions because there is a known bug that will hide
    # certain issues we care about later
    gdal.DontUseExceptions()

    # If a dataset comes back None, then it could not be found / opened and we
    # should fail gracefully
    if dataset is None and raise_error:
        raise Exception('There was an Error locating a threat raster in the '
        'input folder. One of the threat names in the CSV table does not match ' 
        'to a threat raster in the input folder. Please check that the names '
        'correspond. The threat raster that could not be found is : %s', uri)

    return dataset

def make_dictionary_from_csv(csv_uri, key_field):
    """Make a basic dictionary representing a CSV file, where the
       keys are a unique field from the CSV file and the values are
       a dictionary representing each row

       csv_uri - a string for the path to the csv file
       key_field - a string representing which field is to be used
                   from the csv file as the key in the dictionary

       returns - a python dictionary
    """
    out_dict = {}
    csv_file = open(csv_uri)
    reader = csv.DictReader(csv_file)
    for row in reader:
        out_dict[row[key_field]] = row
    csv_file.close()
    return out_dict

def check_projections(ds_dict, proj_unit):
    """Check that a group of gdal datasets are projected and that they are
        projected in a certain unit. 

        ds_dict - a dictionary of gdal datasets
        proj_unit - a float that specifies what units the projection should be
            in. ex: 1.0 is meters.

        returns - False if one of the datasets is not projected or not in the
            correct projection type, otherwise returns True if datasets are
            properly projected
    """
    # a list to hold the projection types to compare later
    projections = []

    for dataset in ds_dict.itervalues():
        srs = osr.SpatialReference()
        srs.ImportFromWkt(dataset.GetProjection())
        if not srs.IsProjected():
            LOGGER.debug('A Raster is Not Projected')
            return False
        if srs.GetLinearUnits() != proj_unit:
            LOGGER.debug('Proj units do not match %s:%s', \
                         proj_unit, srs.GetLinearUnits())
            return False
        projections.append(srs.GetAttrValue("PROJECTION"))
    
    # check that all the datasets have the same projection type
    for index in range(len(projections)):
        if projections[0] != projections[index]:
            LOGGER.debug('Projections are not the same')
            return False

    return True

def threat_names_match(threat_dict, sens_dict, prefix):
    """Check that the threat names in the threat table match the columns in the
        sensitivity table that represent the sensitivity of each threat on a 
        lulc.

        threat_dict - a dictionary representing the threat table:
            {'crp':{'THREAT':'crp','MAX_DIST':'8.0','WEIGHT':'0.7'},
             'urb':{'THREAT':'urb','MAX_DIST':'5.0','WEIGHT':'0.3'},
             ... }
        sens_dict - a dictionary representing the sensitivity table:
            {'1':{'LULC':'1', 'NAME':'Residential', 'HABITAT':'1', 
                  'L_crp':'0.4', 'L_urb':'0.45'...},
             '11':{'LULC':'11', 'NAME':'Urban', 'HABITAT':'1', 
                   'L_crp':'0.6', 'L_urb':'0.3'...},
             ...}

        prefix - a string that specifies the prefix to the threat names that is
            found in the sensitivity table

        returns - False if there is a mismatch in threat names or True if
            everything passes"""

    # get a representation of a row from the sensitivity table where 'sens_row'
    # will be a dictionary with the column headers as the keys
    sens_row = sens_dict[sens_dict.keys()[0]]  
    
    for threat in threat_dict:
        sens_key = prefix + threat
        if not sens_key in sens_row:
            return False
    return True

def biophysical(args):
    """Execute the biophysical component of the habitat_quality model.

       args - a python dictionary with at least the following components:
       args['workspace_dir'] - a uri to the directory that will write output
       args['landuse_dict'] - a python dictionary with keys depicting the
           landuse scenario (current, future, or baseline) and the values GDAL
           datasets.
           {'_c':current dataset, '_f':future dataset, '_b':baseline dataset}
       args['threat_dict'] - a python dictionary representing the threats table
            {'crp':{'THREAT':'crp','MAX_DIST':'8.0','WEIGHT':'0.7'},
             'urb':{'THREAT':'urb','MAX_DIST':'5.0','WEIGHT':'0.3'},
             ... }
       args['sensitivity_dict'] - a python dictionary representing the 
           sensitivity table:
           {'1':{'LULC':'1', 'NAME':'Residential', 'HABITAT':'1', 
                 'L_crp':'0.4', 'L_urb':'0.45'...},
            '11':{'LULC':'11', 'NAME':'Urban', 'HABITAT':'1', 
                  'L_crp':'0.6', 'L_urb':'0.3'...},
             ...}
       args['density_dict'] - a python dictionary that stores any density
           rasters (threat rasters) corresponding to the entries in the threat
           table and whether the density raster belongs to the current, future,
           or baseline raster. Example:
           {'density_c': {'crp' : crp_c.tif, 'srds' : srds_c.tif, ...},
            'density_f': {'crp' : crp_f.tif, 'srds' : srds_f.tif, ...},
            'density_b': {'crp' : crp_b.tif, 'srds' : srds_b.tif, ...}
           }
       args['access_shape'] - an OGR datasource of polygons depicting any 
           protected/reserved land boundaries
       args['half_saturation'] - an float that determines the spread and
           central tendency of habitat quality scores
       args['suffix'] - a string of the desired suffix

       returns nothing."""

    LOGGER.debug('Starting habitat_quality biophysical calculations')

    output_dir = os.path.join(args['workspace_dir'], 'output')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    cur_landuse = args['landuse_dict']['_c']
    threat_dict = args['threat_dict']
    sensitivity_dict = args['sensitivity_dict']
    half_saturation = args['half_saturation']
    suffix = args['suffix'] + '.tif'
       
    out_nodata = -1.0
    
    #Create raster of habitat based on habitat field
    habitat_uri = os.path.join(intermediate_dir, 'habitat' + suffix)
    
    habitat_raster = \
       map_raster_to_dict_values(cur_landuse, habitat_uri, sensitivity_dict, \
                         'HABITAT', out_nodata, 'none')
    
    # If access_lyr: convert to raster, if value is null set to 1, 
    # else set to value
    try:
        LOGGER.debug('Handling Access Shape')
        access_uri = os.path.join(intermediate_dir, 'access_layer' + suffix)
        access_base = \
            raster_utils.new_raster_from_base(cur_landuse, access_uri, \
                'GTiff', out_nodata, gdal.GDT_Float32)
        #Fill raster to all 1's (fully accessible) incase polygons do not cover
        #land area
        access_base.GetRasterBand(1).Fill(1.0)
        access_shape = args['access_shape']
        access_raster = \
                make_raster_from_shape(access_base, access_shape, 'ACCESS')
    except KeyError:
        LOGGER.debug('No Access Shape Provided')
        access_shape = None
        access_raster = access_base

    # calculate the weight sum which is the sum of all the threats weights
    weight_sum = 0.0
    for threat_data in threat_dict.itervalues():
        #Sum weight of threats
        weight_sum = weight_sum + float(threat_data['WEIGHT'])
    
    LOGGER.debug('landuse_dict : %s', args['landuse_dict']) 

    # for each land cover raster provided compute habitat quality
    for lulc_key, lulc_ds in args['landuse_dict'].iteritems():
        LOGGER.debug('Calculating results for landuse : %s', lulc_key)
        
        # get raster properties: cellsize, width, height, 
        # cells = width * height, extent    
        lulc_prop = raster_utils.get_raster_properties(cur_landuse)

        # initialize a list that will store all the density/threat rasters
        # after they have been adjusted for distance, weight, and access
        degradation_rasters = []
       
        # a list to keep track of the normalized weight for each threat
        weight_list = []
        
        # variable to indicate whether we should break out of calculations
        # for a land cover because a threat raster was not found
        exit_landcover = False

        # adjust each density/threat raster for distance, weight, and access 
        for threat, threat_data in threat_dict.iteritems():

            LOGGER.debug('Calculating threat : %s', threat)
            LOGGER.debug('Threat Data : %s', threat_data)
       
            # get the density raster for the specific threat
            threat_raster = args['density_dict']['density' + lulc_key][threat]
       
            if threat_raster == None:
                LOGGER.info(
                'A certain threat raster could not be found for the '
                'Baseline Land Cover. Skipping Habitat Quality '
                'calculation for this land cover.')
                exit_landcover = True
                break
            
            # get the mean cell size, using absolute value because we could
            # get a negative for height or width
            mean_cell_size = \
                (abs(lulc_prop['width']) + abs(lulc_prop['height'])) / 2.0
            
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
           
            filtered_threat_uri = \
               os.path.join(intermediate_dir, threat + '_filtered' + suffix)
            
            # blur the threat raster based on the effect of the threat over
            # distance
            filtered_raster = raster_utils.gaussian_filter_dataset(
                    threat_raster, sigma, filtered_threat_uri, out_nodata)

            # create sensitivity raster based on threat
            sens_uri = \
                os.path.join(intermediate_dir, 
                        'sens_' + threat + lulc_key + suffix )
            
            sensitivity_raster = map_raster_to_dict_values(
                    lulc_ds, sens_uri, sensitivity_dict, 
                    'L_' + threat, out_nodata, 'values_required',
                    error_message='A lulc type in the land cover with ' + \
                    'postfix, ' + lulc_key + ', was not found in the ' + \
                    'sensitivity table. The erroring value was : ')        

            sensitivity_raster.FlushCache()
            
            # get the normalized weight for each threat
            weight_avg = float(threat_data['WEIGHT']) / weight_sum

            # add the threat raster adjusted by distance and the raster
            # representing sensitivity to the list to be past to
            # vectorized_rasters below
            for item in [filtered_raster, sensitivity_raster]:
                degradation_rasters.append(item)

            # store the normalized weight for each threat in a list that
            # will be used below in total_degradation
            weight_list.append(weight_avg)

        # check to see if we got here because a threat raster was missing
        # and if so then we want to skip to the next landcover
        if exit_landcover:
            continue

        def total_degradation(*raster):
            """A vectorized function that computes the degradation value for
                each pixel based on each threat and then sums them together

                *rasters - a list of floats depicting the adjusted threat
                    value per pixel based on distance and sensitivity.
                    The values are in pairs so that the values for each threat
                    can be tracked:
                    [filtered_val_threat1, sens_val_threat1,
                     filtered_val_threat2, sens_val_threat2, ...]
                    There is an optional last value in the list which is the
                    access_raster value, but it is only present if
                    access_raster is not None.

                returns - the total degradation score for the pixel"""

            len_list = len(raster)
            # get the access value 
            access = raster[-1]
            
            sum_degradation = 0.0
            
            # check against nodata values. since we created all the input
            # rasters we know the nodata value will be out_nodata
            if out_nodata in raster:
                return out_nodata

            # loop through the raster list only as many times as there are
            # groups of two. each time calulate the degradation for that threat
            # and compound it to the sum. so at the end of this loop we will
            # have computed the degradation for each threat on the pixel and
            # summed them together

            for index in range(len_list / 2):
                step = index * 2
                sum_degradation += (raster[step] * raster[step + 1] * \
                                    weight_list[index])
            return sum_degradation * access

        # add the access_raster onto the end of the collected raster list. The
        # access_raster will be values from the shapefile if provided or a
        # raster filled with all 1's if not
        degradation_rasters.append(access_raster)
        
        deg_sum_uri = \
            os.path.join(output_dir, 'deg_sum_out' + lulc_key + suffix)

        LOGGER.debug('Starting vectorize on total_degradation') 
        
        sum_deg_raster = \
            raster_utils.vectorize_rasters(degradation_rasters, \
                total_degradation, raster_out_uri=deg_sum_uri, \
                nodata=out_nodata)

        LOGGER.debug('Finished vectorize on total_degradation') 
           
        #Compute habitat quality
        # scaling_param is a scaling parameter set to 2.5 as noted in the users
        # guide
        scaling_param = 2.5
        
        # a term used below to compute habitat quality
        ksq = float(half_saturation**scaling_param)
        
        sum_deg_nodata = \
            sum_deg_raster.GetRasterBand(1).GetNoDataValue()
        
        habitat_nodata = \
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

            return float(habitat) * (1.0 - ((degradation**scaling_param) / \
                (degradation**scaling_param + ksq)))
        
        quality_uri = \
            os.path.join(output_dir, 'quality_out' + lulc_key + suffix)
        
        LOGGER.debug('Starting vectorize on quality_op') 
        
        _ = raster_utils.vectorize_rasters([sum_deg_raster, habitat_raster], 
                quality_op, raster_out_uri=quality_uri, nodata=out_nodata)
        
        LOGGER.debug('Finished vectorize on quality_op') 

    #Compute Rarity if user supplied baseline raster
    try:    
        # will throw a KeyError exception if no base raster is provided
        lulc_base = args['landuse_dict']['_b']
        
        # get the area of a base pixel to use for computing rarity where the 
        # pixel sizes are different between base and cur/fut rasters
        base_properties = raster_utils.get_raster_properties(lulc_base)
        base_area = base_properties['width'] * base_properties['height']

        base_nodata = int(lulc_base.GetRasterBand(1).GetNoDataValue())
        rarity_nodata = float(np.finfo(np.float32).min)
        
        lulc_code_count_b = raster_pixel_count(lulc_base)
        
        # compute rarity for current landscape and future (if provided)
        for lulc_cover in ['_c', '_f']:
            try:
                lulc_x = args['landuse_dict'][lulc_cover]
                
                # get the area of a cur/fut pixel
                lulc_properties = raster_utils.get_raster_properties(lulc_x)
                lulc_area = lulc_properties['width'] * lulc_properties['height']
                
                lulc_nodata = int(lulc_x.GetRasterBand(1).GetNoDataValue())
                
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
                    if base == base_nodata or cover_x == lulc_nodata:
                        return base_nodata
                    return cover_x 
                
                LOGGER.debug('Create new cover for %s', lulc_cover)
                
                new_cover_uri = \
                    os.path.join(intermediate_dir, 
                        'new_cover' + lulc_cover + suffix)
                
                LOGGER.debug('Starting vectorize on trim_op')
                
                # set the current/future land cover to be masked to the base
                # land cover
                new_cover = \
                    raster_utils.vectorize_rasters([lulc_base, lulc_x], trim_op,
                            raster_out_uri=new_cover_uri,
                            datatype=gdal.GDT_Int32, nodata=base_nodata)
                
                LOGGER.debug('Finished vectorize on trim_op')
                
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
                    """Vectorized operation used to map a dictionary to a 
                        lulc raster
                    
                        cover - refers to the 'new_cover' raster generated above
                    
                        return - rarity_nodata if code is not in the dictionary,
                            otherwise return the rarity index pertaining to that
                            code"""
                    if cover in code_index:
                        return code_index[cover]
                    return rarity_nodata
                
                rarity_uri = \
                    os.path.join(output_dir, 'rarity' + lulc_cover + suffix)
               
                LOGGER.debug('Starting vectorize on map_ratio')
               
                _ = raster_utils.vectorize_rasters([new_cover], map_ratio, \
                        raster_out_uri=rarity_uri, nodata=rarity_nodata)
               
                LOGGER.debug('Finished vectorize on map_ratio')
                
            except KeyError:
                continue
    
    except KeyError:
        LOGGER.info('Baseline not provided to compute Rarity')

    LOGGER.debug('Finished habitat_quality biophysical calculations')

def raster_pixel_count(dataset):
    """Determine how many of each unique pixel lies in the dataset (dataset)
    
        dataset - a GDAL raster dataset

        returns -  a dictionary whose keys are the unique pixel values and whose
                   values are the number of occurrences
    """
    LOGGER.debug('Entering raster_pixel_count')
    band = dataset.GetRasterBand(1)
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

    LOGGER.debug('Leaving raster_pixel_count')
    return counts

def make_raster_from_shape(base_raster, shape, attr):
    """Burn an attribute value from a polygon shapefile onto an
       existing blank raster

       base_raster - a gdal raster dataset to burn the shapefile
                     values onto
       shape - a ORG datasource polygon shapefile
       attr - a python string of the attribute field to burn values
              from

       returns - a GDAL raster dataset"""
    LOGGER.debug('Entering make_raster_from_shape')
    
    attribute_string = 'ATTRIBUTE=' + attr
    gdal.RasterizeLayer(base_raster, [1], shape.GetLayer(0),
                        options = [attribute_string])
    LOGGER.debug('Leaving make_raster_from_shape')

    return base_raster 
       
def map_raster_to_dict_values(key_raster, out_uri, attr_dict, field, \
        out_nodata, raise_error, error_message='An Error occured mapping' + \
        'a dictionary to a raster'):
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
       raise_error - a string that decides how to handle the case where the
           value from 'key_raster' is not found in 'attr_dict'. If 'raise_error'
           is 'values_required', raise Exception, if 'none', return 'out_nodata'
       error_message - a string that is printed out with the raised Exception if
           'raise_error' is set to True

       returns - a GDAL raster, or raises an Exception and fail if:
           1) raise_error is True and
           2) the value from 'key_raster' is not a key in 'attr_dict'
    """

    LOGGER.debug('Starting map_raster_to_dict_values')
    int_attr_dict = {}
    for key in attr_dict:
        int_attr_dict[int(key)] = float(attr_dict[key][field])

    reclassified_dataset = raster_utils.reclassify_dataset(
        key_raster, int_attr_dict, out_uri, gdal.GDT_Float32, out_nodata,
        exception_flag=raise_error)

    return reclassified_dataset
