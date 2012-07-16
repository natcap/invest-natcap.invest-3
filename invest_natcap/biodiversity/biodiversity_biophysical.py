"""InVEST Biophysical model file handler module"""
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import csv

from invest_natcap.biodiversity import biodiversity_core

import os.path
import logging

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
        args['threat_uri'] - a uri to an input CSV containing data
            of all the considered threats. Each row is a degradation source
            and each column a different attribute of the source with the
            following names: 'THREAT','MAX_DIST','WEIGHT','DECAY' (required).
        args['access_uri'] - a uri to an input polygon shapefile containing
            data on the relative protection against threats (optional)
        args['sensitivity_uri'] - a uri to an input CSV file of LULC types,
            whether they are considered habitat, and their sensitivity to each
            threat (required)
        args['half_saturation_constant'] - a python integer that determines
            the spread and central tendency of habitat quality scores 
            (required)
        args['results_suffix'] - a python string that will be inserted into all
            raster uri paths just before the file extension.

        returns nothing."""

    workspace = args['workspace_dir']
    
    biophysical_args = {}
    biophysical_args['workspace_dir'] = workspace
    # If the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = args['results_suffix']
    except:
        suffix = ''

    # Check to see if each of the workspace folders exists.  If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')
    input_dir = os.path.join(workspace, 'input')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    biophysical_args['threat_dict'] = \
        make_dictionary_from_csv(args['threat_uri'],'Threat')

    biophysical_args['sensitivity_dict'] = \
        make_dictionary_from_csv(args['sensitivity_uri'],'LULC')

    biophysical_args['half_saturation'] = int(args['half_saturation_constant'])    

    # if the access shapefile was provided add it to the dictionary
    try:
        biophysical_args['access_shape'] = ogr.Open(args['access_uri'])
    except KeyError:
        pass

    # Determine which land cover scenarios we should run, and append the
    # appropriate suffix to the landuser_scenarios list as necessary for the
    # scenario.
    landuse_scenarios = {'cur':'_c'}
    for lu_uri, lu_time, lu_ext in ('landuse_fut_uri','fut','_f'),('landuse_bas_uri','bas','_b'):
        if lu_uri in args:
            landuse_scenarios[lu_time] = lu_ext

    # declare dictionaries to store the land cover rasters and the density
    # rasters pertaining to the different threats
    landuse_dict = {}
    density_dict = {}

    resolutions = []

    # for each possible land cover the was provided try opening the raster and
    # adding it to the dictionary. Also compile all the threat/density rasters
    # associated with the land cover
    for scenario, ext in landuse_scenarios.iteritems():
        landuse_dict[ext] = \
            gdal.Open(str(args['landuse_'+scenario+'_uri']), gdal.GA_ReadOnly)
        
        resolutions.append(get_raster_resolution(landuse_dict[ext]))        

        # add a key to the density dictionary that associates all density/threat
        # rasters with this land cover
        density_dict['density'+ext] = {}

        # for each threat given in the CSV file try opening the associated
        # raster which should be found in workspace/input/
        for threat in biophysical_args['threat_dict']:
            try:
                density_dict['density'+ext][str(threat)] = \
                    open_ambiguous_raster(os.path.join(input_dir, threat+ext))
            except:
                LOGGER.warn('Error encountered getting raster for threat : %s',
                            os.path.join(input_dir, threat+ext))
    
    biophysical_args['landuse_dict'] = landuse_dict
    biophysical_args['density_dict'] = density_dict

    quit_model = False
    
    # checking to make sure the land covers have the same projections and are
    # projected in meters
    quit_model = check_projections(landuse_dict, 1.0)
    
    LOGGER.debug('Resolutions : %s', resolutions)
    for index in range(len(resolutions)):
        if resolutions[0] != resolutions[index]:
            LOGGER.error(str('The resolutions between the land cover rasters were\
                          not the same, please make sure they all have the\
                          same resolutions'))
            quit_model = True

    if not quit_model:
        biodiversity_core.biophysical(biophysical_args)

def open_ambiguous_raster(uri):
    """Open and return a gdal dataset given a uri path that includes the file
        name but not neccessarily the suffix or extension of how the raster may
        be represented.

        uri - a pythong string of the file path that includes the name of the
              file but not it's extension

        return - a gdal dataset or NONE if no file is found with the pre-defined
                 suffixes and 'uri'"""
    # a list of possible suffixes for raster datasets. We currently can handle
    # .tif and directory paths
    possible_suffixes = ['', '.tif']
    
    # initialize dataset to None in the case that all paths do not exist
    dataset = None 
    for suffix in possible_suffixes:
        if not os.path.exists(uri+suffix):
            continue
        dataset = gdal.Open(uri+suffix, gdal.GA_ReadOnly)
        # return as soon as a valid gdal dataset is found
        if dataset is not None:
            break

    #LOGGER.debug('DATASET : %s, %s', dataset, uri)
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
    
def get_raster_resolution(dataset):
    """Get the resolution or the pixel size of the dataset and return it as a
       tupple (col_width, row_width)

       dataset - a GDAL raster dataset

       returns a tupple of the column and row width in that order
    """

    gt = dataset.GetGeoTransform()
    col_width = int(gt[1])
    row_width = int(gt[5])
    return (col_width, row_width)

def check_projections(ds_dict, proj_unit):
    """Check that a group of gdal datasets are projected and that they are
        projected in a certain unit. 

        ds_dict - a dictionary of gdal datasets
        proj_unit - a float that specifies what units the projection should be
            in. ex: 1.0 is meters.

        returns - true if one of the datasets is not projected or not in the
            correct projection type, otherwise returns false if datasets are
            properly projected
    """
    # a list to hold the projection types to compare later
    projections = []

    for ds in ds_dict.itervalues():
        srs = osr.SpatialReference()
        srs.ImportFromWkt(ds.GetProjection())
        if not srs.IsProjected():
            return True
        if srs.GetLinearUnits() != proj_unit:
            return True
        projections.append(srs.GetAttrValue("PROJECTION"))
    
    # check that all the datasets have the same projection type
    for index in range(len(projections)):
        if projections[0] != projections[index]:
            return True

    return False



