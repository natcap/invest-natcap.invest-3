"""InVEST Biophysical model file handler module"""
import glob
from osgeo import gdal
from osgeo import ogr
import csv

from invest_natcap.biodiversity import biodiversity_core
from invest_natcap.iui import fileio

import os.path
import re
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
            (optional)
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
    
    landuse_dict = {}
    
    for scenario, ext in landuse_scenarios.iteritems():
        landuse_dict[ext] = \
            gdal.Open(str(args['landuse_'+scenario+'_uri']), gdal.GA_ReadOnly)
        
        density_dict = {}
        
        for threat in biophysical_args['threat_dict']:
            try:
                density_dict['density'+ext][str(threat)] = \
                    open_ambiguous_raster(os.path.join(input_dir, threat+ext))
            except:
                LOGGER.warn('Error encountered getting raster threat : %s',
                            os.path.join(input_dir, threat+ext))
    
    biophysical_args['landuse_dict'] = landuse_dict
    biophysical_args['density_dict'] = density_dict

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
    
    for suffix in possible_suffixes:
        if not os.path.exists(uri+suffix):
            continue
        dataset = gdal.Open(uri+suffix, gdal.GA_ReadOnly)
        if dataset is not None:
            break
     
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
    





