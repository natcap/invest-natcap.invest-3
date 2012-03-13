"""Module that contains the core computational components for the hydropower
    model including the water yield, water scarcity , and valuation functions"""

import logging
import os

import numpy as np
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('sediment_core')

def water_yield(args):
    """Executes the water_yield model
    
        args - is a dictionary with at least the following entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc'] - a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['soil_depth'] - an input raster describing the 
            average soil depth value for each cell (mm) (required)
        args['precipitation'] - an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        args['pawc'] - an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        args['ape'] - an input raster describing the 
            annual average evapotranspiration value for each cell. Potential
            evapotranspiration is the potential loss of water from soil by
            both evaporation from the soil and transpiration by healthy Alfalfa
            (or grass) if sufficient water is available (mm) (required)
        args['watersheds'] - an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds'] - an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['biophysical_dictionary'] - an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth and etk. NOTE: these data are 
            attributes of each LULC class rather than attributes of individual 
            cells in the raster map (required)
        args['zhang'] - floating point value between 1 and 10 corresponding
            to the seasonal distribution of precipitation (required)
            
        returns nothing"""
        
    #water yield functionality goes here
    LOGGER.info('Starting Water Yield Calculation')
    workspace_dir = args['workspace_dir']
    #Construct folder paths
    output_dir = workspace_dir + os.sep + 'Output'
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    service_dir = workspace_dir + os.sep + 'Service'
    
    bio_dict = args['biophysical_dictionary']
    lulc_raster = args['lulc']
    ape_raster = args['ape']
    precip_raster = args['precipitation']
    
    #brute force create raster from table values
    tmp_etk_path = intermediate_dir + os.sep + 'tmp_etk_path.tiff'
    tmp_etk_raster = create_etk_root_rasters(lulc_raster, tmp_etk_path, 255.0,
                                             bio_dict, 'etk')
    
    def op(etk, ape, precip):
        val = (etk * ape) / 1000
        result = val / precip
        return result
    
    tmp_DI = intermediate_dir + os.sep + 'tmp_DI.tiff'
    tmp_DI_raster = \
        invest_core.vectorizeRasters([tmp_etk_raster, ape_raster, precip_raster],
                                     op, rasterName=tmp_DI)
    
    #brute force create raster from table values
    tmp_root_path = intermediate_dir + os.sep + 'tmp_root_path.tiff'
    tmp_root_raster = create_etk_root_rasters(lulc_raster, tmp_root_path, 255.0,
                                             bio_dict, 'root_depth')
    
    
def create_etk_root_rasters(key_raster, new_path, nodata, bio_dict, field):
    #brute force create raster from table values
    tmp_raster = \
        invest_cython_core.newRasterFromBase(key_raster, new_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
    key_band = key_raster.GetRasterBand(1)
    key_nodata = key_band.GetNoDataValue()
    array = key_band.ReadAsArray()
    #http://stackoverflow.com/questions/3403973/fast-replacement-of-values-in-a-numpy-array
    new_array = np.copy(array)
    for k, v in bio_dict.iteritems(): 
        new_array[array==k] = v['etk']
    
    tmp_band = tmp_raster.GetRasterBand(1)
    tmp_band.WriteArray(new_array)
    return tmp_raster

def water_scarcity(args):
    #water yield functionality goes here    
    LOGGER.info('Starting Water Scarcity Calculation')
        
def valuation(args):
    #water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')