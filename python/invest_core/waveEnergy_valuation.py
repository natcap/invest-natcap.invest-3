"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_core
import invest_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy as np
from dbfpy import dbf

import csv

def execute(args):
    """This function invokes the valuation part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy valuation processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['land_gridPts_uri'] - A CSV file path for the landing and grid point coordinates
        args['machine_econ_uri'] - A CSV file path for the machine economic parameters
        args['numberOfMachines'] - An integer specifying the number of machines
        args['projection_uri'] - A path for the projection to transform coordinates from decimal degrees to meters
        args['captureWE'] - We need the captured wave energy output from biophysical run.
        args['globa_dem'] - We need the depth of the locations for calculating costs
        """
        
    #This ensures we are not in Arc's python directory so that when
    #we import gdal stuff we don't get the wrong GDAL version.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()
    
    valuationargs = []
    
    #Open/create the output directory
    
    #Read machine economic parameters into a dictionary
    try:
        machine_econ = {}
        machineEconFile = open(args['machine_econ_uri'])
        reader = csv.DictReader(machineEconFile)
        for row in reader:
            machine_econ[row['NAME'].strip()] = row
        machineEconFile.close()
        valuationargs['machine_econ'] = machine_econ
    except IOError, e:
        print 'File I/O error' + e
    #Read landing and power grid connection points into a dictionary
    try:
        landGridPts = {}
        landGridPtsFile = open(args['land_gridPts_uri'])
        reader = csv.DictReader(landGridPtsFile)
        for row in reader:
            landGridPts[row['ID'].strip()] = row
        landGridPtsFile.close()
        valuationargs['machine_param'] = landGridPts
    except IOError, e:
        print 'File I/O error' + e
    #Open the output files for capturedWE from the biophysical run
    
    #Open the file that contains the depth values
    
    #Call the valuation core module with attached arguments to run the economic valuation