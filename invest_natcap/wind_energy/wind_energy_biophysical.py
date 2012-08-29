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

LOGGER = logging.getLogger('wind_energy_biophysical')

def execute(args):
    """This is where the doc string lives
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved
        args[aoi_uri] - a uri to an OGR shapefile that specifies the area of
            interest for the wind data points
        args[bathymetry_uri] - a uri to a GDAL raster dataset that has the depth
            values of the area of interest
        args[bottom_type_uri] - a uri to an OGR shapefile that depicts the
            subsurface geology type
        args[hub_height] - a float value that is the hub height
        args[pwr_law_exponent] - a float value for the power law exponent
        args[cut_in_wspd] - a float value for the cut in wind speed of the
            turbine
        args[rated_wspd] - a float value for the rated wind speed
        args[cut_out_wspd] - a float value for the cut out wind speed of the
            turbine
        args[turbine_rated_pwr] - a float value for the turbine rated power
        args[exp_output_pwr_curve] - a float value exponent output power curve
        args[days] - a float value for the number of days
        args[air_density] - a float value for the air density constant
        args[min_depth] - a float value minimum depth of the device
        args[max_depth] - a float value maximum depth of the device
    
        returns -  
    """

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

    # handle opening of relevant files

    # handle any pre-processing that must be done

    # call on the core module
