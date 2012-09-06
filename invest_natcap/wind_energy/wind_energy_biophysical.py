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
        args[min_distance] - 
        args[max_distance] - 
        args[land_polygon_uri] -

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
    bathymetry = gdal.Open(args['bathymetry_uri'])
    biophysical_args['bathymetry'] = bathymetry

    aoi = ogr.Open(args['aoi_uri'])
    biophysical_args['aoi'] = aoi 

    
    biophysical_args['min_depth'] = float(args['min_depth']) 
    biophysical_args['max_depth'] = float(args['max_depth'])
    try:
        LOGGER.debug('Distances : %s:%s',
                float(args['min_distance']), float(args['max_distance']))
        biophysical_args['min_distance'] = float(args['min_distance']) 
        biophysical_args['max_distance'] = float(args['max_distance'])
        biophysical_args['land_polygon'] = gdal.Open(args['land_polygon_uri'])
    except KeyError:
        LOGGER.debug("Distance information not selected")
        pass

    # handle any pre-processing that must be done

    # call on the core module

    wind_energy_core.biophysical(biophysical_args)

def read_wind_data(wind_data_uri):
    """Unpack the wind data into a dictionary

        wind_data_uri - a uri for the wind data text file

        returns - a dictionary where the keys is the row number and the values
            are dictionaries mapping column headers to values """

    wind_file = open(wind_data_uri)
    columns_line = wind_file.readline().split(',')
    wind_dict = {}
    
    for line in wind_file.readlines():
        line_array = line.split(',')
        key = line_array[0]
        wind_dict[key] = {}
        for index in range(1, len(line_array) - 1):
            wind_dict[key][columns_line[index]] = float(line_array[index])

    wind_file.close()

    LOGGER.debug(
        'wind_dict keys : %s', np.sort(np.array(wind_dict.keys()).astype(int)))
    
    return wind_dict







