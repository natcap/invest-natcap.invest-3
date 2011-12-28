"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import math

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
        args['v_stream_out'] - An output raster file that classifies the
            watersheds into stream and non-stream regions based on the
            value of 'threshold_flow_accumulation'
            
        returns nothing"""

    LOGGER.info("do it up")

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    LOGGER.info('do it up')

def flow_direction_inf(dem, flow):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.

       dem - (input) a single band raster with elevation values
       flow - (output) a single band float raster of same dimensions as
           dem.  After the function call it will have flow direction in it 
       
       returns nothing"""

    nodataDem = dem.GetRasterBand(1).GetNoDataValue()
    nodataFlow = flow.GetRasterBand(1).GetNoDataValue()

    #GDal inverts x and y, so it's easier to transpose in and back out later
    #on gdal arrays, so we invert the x and y offsets here
    demMatrixTmp = dem.GetRasterBand(1).ReadAsArray(0, 0, dem.RasterXSize, \
        dem.RasterYSize).transpose()

    #Incoming matrix type could be anything numerical.  Cast to a floating
    #point for cython speed and because it's the most general form.
    demMatrix = demMatrixTmp.astype(np.float)
    demMatrix[:] = demMatrixTmp

    xmax, ymax = demMatrix.shape[0], demMatrix.shape[1]

    #This matrix holds the flow direction value, initialize to zero
    flowMatrix = np.zeros([xmax, ymax], dtype=np.float)

    #loop through each cell and skip any edge pixels
    for x in range(1, xmax - 1):
        for y in range(1, ymax - 1):
            #Algorithm goes in here
            flowMatrix[x, y] = .0

    flow.GetRasterBand(1).WriteArray(flowMatrix.transpose(), 0, 0)
