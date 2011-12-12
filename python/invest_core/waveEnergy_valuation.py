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
    """This function invokes the biophysical part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['landPowergridpts_uri'] - 
        args['machine_econParams_uri'] - 
        args['numberOfMachines'] - 
        args['projection_uri'] - 
        
        """
        