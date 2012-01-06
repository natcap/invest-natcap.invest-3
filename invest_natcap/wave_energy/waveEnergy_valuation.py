"""InVEST Wave Energy Model file handler module"""

import sys
import os
import csv

import simplejson as json
import numpy as np
from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *

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
        args['attribute_shape_path']
        """

    filesystemencoding = sys.getfilesystemencoding()

    valuationargs = {}
    valuationargs['workspace_dir'] = args['workspace_dir']
    valuationargs['projection'] = args['projection_uri']
    valuationargs['global_dem'] = gdal.Open(args['global_dem'])
    valuationargs['capturedWE'] = gdal.Open(args['capturedWE'])
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
        valuationargs['land_gridPts'] = landGridPts
    except IOError, e:
        print 'File I/O error' + e
    #It may be easiest to have capturedWE and Depth in shapefile and
    #have that shapefile be named something specific so that we can
    #differentiate between whether AOI was used or not.  If not, then
    #report an error back saying that the biophysical model must be run
    #with AOI for valuation to be run.
    #If the above is the case, then:
    attribute_shape = ogr.Open(args['attribute_shape_path'])    
    valuationargs['attribute_shape'] = attribute_shape
    
    #Open the output files for capturedWE from the biophysical run

    #Open the file that contains the depth values
    
    #Add the number of machines to arguments for valuation
    valuationargs['number_machines'] = args['numberOfMachines']
    #Not sure whether the projection should be taken care of here or in valuation
        #Handle projection transformation here if necessary
        
    #Call the valuation core module with attached arguments to run the economic valuation
    waveEnergy_core.valuation(valuationargs)