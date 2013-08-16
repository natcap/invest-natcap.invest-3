"""InVEST Biophysical model file handler module"""
import os.path
import logging
import csv

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.biodiversity import biodiversity_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('biodiversity_biophysical')

def execute(args):
    """Open files necessary for the biophysical portion of the biodiversity
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

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

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
                density_dict['density' + ext][threat] = \
                    open_ambiguous_raster(os.path.join(input_dir, threat + ext))
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

    biodiversity_core.biophysical(biophysical_args)

def open_ambiguous_raster(uri):
    """Open and return a gdal dataset given a uri path that includes the file
        name but not neccessarily the suffix or extension of how the raster may
        be represented.

        uri - a python string of the file path that includes the name of the
              file but not its extension

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
        full_uri = uri +  suffix
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
    if dataset is None:
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
