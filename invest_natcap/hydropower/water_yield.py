"""InVEST Water Yield module at the "uri" level"""

import logging

from invest_natcap.hydropower import hydropower_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('water_yield')

def execute(args):
    """This is point of entry to pass along the arguments to water_yield model
        in hydropower_core.water_yield
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexes in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape. (required)
        args['soil_depth_uri'] - a uri to an input raster describing the 
            average soil depth value for each cell (mm) (required)
        args['precipitation_uri'] - a uri to an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        args['pawc_uri'] - a uri to an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        args['eto_uri'] - a uri to an input raster describing the 
            annual average evapotranspiration value for each cell. Potential
            evapotranspiration is the potential loss of water from soil by
            both evaporation from the soil and transpiration by healthy Alfalfa
            (or grass) if sufficient water is available (mm) (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['biophysical_table_uri'] - a uri to an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth (mm) and etk, which are required. 
            NOTE: these data are attributes of each LULC class rather than 
            attributes of individual cells in the raster map (required)
        args['seasonality_constant'] - floating point value between 1 and 10 
            corresponding to the seasonal distribution of precipitation 
            (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
           
        returns - nothing"""
    
    LOGGER.info('Starting Water Yield File Handling')
    
    #Call water_yield in hydropower_core.py
    hydropower_core.water_yield(args)
    LOGGER.info('Water Yield Completed')
