"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import math

import numpy as np
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('sediment_core')

def biophysical(args):
    """Executes the basic sediment model

        args - is a dictionary with at least the following entries:
        args['dem'] - a digital elevation raster file (required)
        args['erosivity'] - an input raster describing the 
            rainfall eroisivity index (required)
        args['erodibility'] - an input raster describing soil 
            erodibility (required)
        args['landuse'] - a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['watersheds'] - an input shapefile of the watersheds
            of interest as polygons. (required)
        args['subwatersheds'] - an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds' shape provided as input. (required)
        args['usle_uri'] - a URI location to the temporary USLE raster
        args['reservoir_locations'] - an input shape file with 
            points indicating reservoir locations with IDs. (optional)
        args['reservoir_properties'] - an input CSV table 
            describing properties of input reservoirs provided in the 
            reservoirs shapefile (optional)
        args['biophysical_table'] - an input CSV file with 
            biophysical information about each of the land use classes.
        args['threshold_flow_accumulation'] - an integer describing the number
            of upstream cells that must flow int a cell before it's considered
            part of a stream.  required if 'v_stream' is not provided.
        args['slope_threshold'] - A percentage slope threshold as described in
            the user's guide.
        args['slope'] - an output raster file that holds the slope percentage
            as a proporition from the dem
        args['ls_factor'] - an output raster file containing the ls_factor
            calculated on the particular dem
        args['v_stream_out'] - An output raster file that classifies the
            watersheds into stream and non-stream regions based on the
            value of 'threshold_flow_accumulation'
        args['flow_direction'] - An output raster indicating the flow direction on each
            pixel
            
        returns nothing"""

    LOGGER.info("calculating flow direction")
    invest_cython_core.flow_direction_inf(args['dem'], args['flow_direction'])

    LOGGER.info("calculating flow accumulation")
    invest_cython_core.flow_accumulation_dinf(args['flow_direction'],
                                              args['flow_accumulation'],
                                              args['dem'])

    invest_cython_core.calculate_slope(args['dem'], args['slope'])

    LOGGER.info("calculating LS factor accumulation")
    invest_cython_core.calculate_ls_factor(args['flow_accumulation'],
                                           args['slope'],
                                           args['flow_direction'],
                                           args['ls_factor'])

    #Nodata value to use for output raster
    usle_nodata = -1.0

    #map lulc to a usle_c * usle_p raster
    LOGGER.info('mapping landuse types to crop and practice management values')
    usle_c_p_raster = invest_cython_core.newRasterFromBase(args['landuse'], '',
        'MEM', usle_nodata, gdal.GDT_Float32)
    def lulc_to_cp(lulc_code):
        #There are string casts here because the biophysical table is all 
        #strings thanks to the csv table conversion.
        if str(lulc_code) not in args['biophysical_table']:
            return usle_nodata
        #We need to divide the c and p factors by 1000 (10*6 == 1000*1000) 
        #because they're stored in the table as C * 1000 and P * 1000.  See 
        #the user's guide:
        #http://ncp-dev.stanford.edu/~dataportal/invest-releases/documentation/2_2_0/sediment_retention.html
        return float(args['biophysical_table'][str(lulc_code)]['usle_c']) * \
            float(args['biophysical_table'][str(lulc_code)]['usle_p']) / 10 ** 6
    invest_core.vectorize1ArgOp(args['landuse'].GetRasterBand(1), lulc_to_cp,
                                usle_c_p_raster.GetRasterBand(1))

    #Set up structures for USLE calculation
    ls_nodata = args['ls_factor'].GetRasterBand(1).GetNoDataValue()
    erosivity_nodata = args['erosivity'].GetRasterBand(1).GetNoDataValue()
    erodibility_nodata = args['erodibility'].GetRasterBand(1).GetNoDataValue()
    def mult_all(ls_factor, erosivity, erodibility, usle_c_p):
        if ls_factor == usle_nodata or erosivity == usle_nodata or \
            erodibility == usle_nodata or usle_c_p == usle_nodata:
            return usle_nodata
        return ls_factor * erosivity * erodibility * usle_c_p
    op = np.vectorize(mult_all)
    LOGGER.info("calculating potential soil loss")
    invest_core.vectorizeRasters([args['ls_factor'], args['erosivity'],
        args['erodibility'], usle_c_p_raster], op, args['usle_uri'],
                                 nodata=usle_nodata)

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    LOGGER.info('do it up')
