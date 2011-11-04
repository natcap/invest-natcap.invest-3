"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_core
import invest_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

from xlrd import open_workbook

def execute(args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['wave_base_data_uri'] - a boolean, True if sequestration
            is to be calculated.  Infers that args['lulc_fut_uri'] should be 
            set.
        args['analysis_area_uri'] - a boolean, True if harvested wood product
            calcuation is to be done.  Also implies a sequestration 
            calculation.  Thus args['lulc_fut_uri'], args['hwp_cur_shape_uri'],
            args['AOI_uri'], args['lulc_cur_year'], and 
            args['machine_perf_uri'] should be set.
        args['AOI_uri'] - a Boolean.  True if we wish to calculate 
            uncertainty in the carbon model.  Implies that carbon pools should
            have value ranges
        args['machine_perf_uri'] - the percentile cutoff desired for 
            uncertainty calculations (required if args['calc_uncertainty'] is 
            True) 
        args['machine_param_uri'] - is a uri to a GDAL raster dataset (required)
        args['dem_uri'] - is a uri to a GDAL raster dataset (required
         if calculating sequestration or HWP)
        args['calculate_valuation'] - An integer representing the year of lulc_cur 
            used in HWP calculation (required if args['calculate_hwp'] is True)
        args['landgridpts_uri'] - An integer representing the year of  lulc_fut
            used in HWP calculation (required if args['calculate_hwp'] is True)
        args['machine_econ_uri'] - is a uri to a DBF dataset mapping carbon 
            storage density to the lulc classifications specified in the
            lulc rasters.  If args['calc_uncertainty'] is True the columns
            should have additional information about min, avg, and max carbon
            pool measurements. 
        args['number_machines'] - Current shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True) 
        args['projection'] - Future shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True)
        
        returns nothing."""

    #This ensures we are not in Arc's python directory so that when
    #we import gdal stuff we don't get the wrong GDAL version.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    gdal.AllRegister()

    machine_perf = open_workbook(args['machine_perf_uri'])
    machine_param = open_workbook(args['machine_param_uri'])
    
    arguments = {'output_dir': gp.GetParameterAsText(0),
             'wave_base_data_uri': gp.GetParameterAsText(1),
             'analysis_area_uri': gp.GetParameterAsText(2),
             'AOI_uri': gp.GetParameterAsText(3),
             'machine_perf_uri': float(gp.GetParameterAsText(4)),
             'machine_param_uri': gp.GetParameterAsText(5),
             'dem_uri': gp.GetParameterAsText(6),
#             'valuation': gp.GetParameterAsText(7),
#             'landgridpts_uri': gp.GetParameterAsText(8),
#             'machine_econ_uri': gp.GetParameterAsText(9),
#             'number_machines': gp.GetParameterAsText(10),
#             'projection_uri': gp.GetParameterAsText(11)
            }
    
    waveEnergy_core.execute(arguments)