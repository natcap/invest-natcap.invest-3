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
    soil_depth_raster = args['soil_depth']
    pawc_raster = args['pawc']
    zhang = float(args['zhang'])
    #brute force create raster from table values
    tmp_etk_path = intermediate_dir + os.sep + 'tmp_etk_path.tiff'
    tmp_etk_raster = create_etk_root_rasters(lulc_raster, tmp_etk_path, 255.0,
                                             bio_dict, 'etk')
    
    #brute force create raster from table values
    tmp_root_path = intermediate_dir + os.sep + 'tmp_root_path.tiff'
    tmp_root_raster = create_etk_root_rasters(lulc_raster, tmp_root_path, 255.0,
                                             bio_dict, 'root_depth')
   
    def op(etk, ape, precip, root, soil, pawc):
        val = (etk * ape) / 1000
        tmp_DI = val / precip
        
        awc = (np.minimum(root, soil) * pawc)
        
        tmp_w = (awc / (precip + 1)) * zhang
        
        tmp_max_aet = np.copy(tmp_DI)
        np.putmask(tmp_max_aet, tmp_max_aet > 1, 1)
        
        tmp_calc = ((tmp_w * tmp_DI + 1) / (( 1/ tmp_DI) + (tmp_w * tmp_DI + 1)))
        fractp = np.minimum(tmp_max_aet, tmp_calc)
        return fractp
    
    fractp_path = intermediate_dir + os.sep + 'fractp.tif'
    raster_list = [tmp_etk_raster, ape_raster, precip_raster, tmp_root_raster,
                   soil_depth_raster, pawc_raster]
    fractp_raster = \
        invest_core.vectorizeRasters(raster_list, op, rasterName=fractp_path)

    
def create_etk_root_rasters(key_raster, new_path, nodata, bio_dict, field):
    #brute force create raster from table values
    tmp_raster = \
        invest_cython_core.newRasterFromBase(key_raster, new_path, 
                                            'GTiff', nodata, gdal.GDT_Float32)
    key_band = key_raster.GetRasterBand(1)
    key_nodata = key_band.GetNoDataValue()
    array = key_band.ReadAsArray()
    #http://stackoverflow.com/questions/3403973/fast-replacement-of-values-in-a-numpy-array
    new_array = array.astype(np.float)
    for k, v in bio_dict.iteritems(): 
        new_array[array==int(k)] = float(v[field])
        if k=='57':
            LOGGER.debug('new_array : %s : %s', k, v)
    LOGGER.debug('new_array')
    tmp_band = tmp_raster.GetRasterBand(1)
    tmp_band.WriteArray(new_array, 0, 0)
    return tmp_raster

def water_scarcity(args):
    #water yield functionality goes here    
    LOGGER.info('Starting Water Scarcity Calculation')
        
def valuation(args):
    #water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')