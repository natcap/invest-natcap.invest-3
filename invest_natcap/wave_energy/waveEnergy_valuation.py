"""InVEST Wave Energy Model file handler module"""

import sys
import os
import csv

import simplejson as json
import numpy as np
from osgeo import ogr
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core
from invest_natcap.wave_energy import waveEnergy_core

def execute(args):
    """This function invokes the valuation part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy valuation processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['land_gridPts_uri'] - A CSV file path containing the Landing and Power Grid Connection Points table.
        args['machine_econ_uri'] - A CSV file path for the machine economic parameters table.
        args['numberOfMachines'] - An integer specifying the number of machines.
        args['projection_uri'] - A path for the projection to transform coordinates from decimal degrees to meters.
        args['captureWE'] - We need the captured wave energy output from biophysical run.
        args['globa_dem'] - We need the depth of the locations for calculating costs.
        args['wave_data_shape_path'] - The path to the point shapefile created during biophysical run.
        """

    valuation_args = {}
    valuation_args['workspace_dir'] = args['workspace_dir']
    valuation_args['projection'] = args['projection_uri']
    valuation_args['global_dem'] = gdal.Open(args['global_dem'])
    valuation_args['capturedWE'] = gdal.Open(args['capturedWE'])
    valuation_args['wave_data_shape'] = ogr.Open(args['wave_data_shape_path'])
    valuation_args['number_machines'] = args['numberOfMachines']
    #Open/create the output directory
    output_dir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediate_dir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for dir in [output_dir, intermediate_dir]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    #Read machine economic parameters into a dictionary
    try:
        machine_econ = {}
        machine_econ_file = open(args['machine_econ_uri'])
        reader = csv.DictReader(machine_econ_file)
        for row in reader:
            machine_econ[row['NAME'].strip()] = row
        machine_econ_file.close()
        valuation_args['machine_econ'] = machine_econ
    except IOError, e:
        print 'File I/O error' + e
    #Read landing and power grid connection points into a dictionary
    try:
        land_grid_pts = {}
        land_grid_pts_file = open(args['land_gridPts_uri'])
        reader = csv.DictReader(land_grid_pts_file)
        for row in reader:
            land_grid_pts[row['ID'].strip()] = row
        land_grid_pts_file.close()
        valuation_args['land_gridPts'] = land_grid_pts
    except IOError, e:
        print 'File I/O error' + e

    #Call the valuation core module with attached arguments to run the economic valuation
    waveEnergy_core.valuation(valuation_args)
