"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_valuation')

def execute(args):
    """Takes care of all file handling for the valuation part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[biophysical_data_uri] - a uri to an OGR datasource of type point
            from the output of the biophysical model run (required) 
        args[turbine_info_uri] - a uri to a CSV file that has the parameters
            for the type of turbine (required)
        args[grid_points_uri] - a uri to a CSV file that specifies the landing
            and grid point locations (optional)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required)
        args[suffix] - a string for the suffix to be appended to the output
            names (optional) 
    
        returns - nothing
    """

    # create output folders
    workspace = args['workspace_dir']
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # handle suffix
    try:
        suffix = '_' + args['suffix']
    except KeyError:
        suffix = ''

    # handle opening of relevant files
    turbine_dict = {}
    turbine_file = open(args['turbine_info_uri'])
    reader = csv.DictReader(turbine_file)

    # Making a shallow copy of the attribute 'fieldnames' explicitly to edit to
    # all the fields to lowercase because it is more readable and easier than
    # editing the attribute itself
    field_names = reader.fieldnames

    for index in range(len(field_names)):
        field_names[index] = field_names[index].lower()

    for row in reader:
        turbine_dict[row['type']] = row
    turbine_file.close()
    LOGGER.debug('Turbine Dictionary: %s', turbine_dict)

    # handle any pre-processing that must be done

    # call on the core module
