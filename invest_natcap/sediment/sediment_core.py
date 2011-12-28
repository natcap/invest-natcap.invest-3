"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import math

import numpy as np

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
        args['flow'] - An output raster indicating the flow direction on each
            pixel
            
        returns nothing"""

    LOGGER.info("calculating flow direction")
    flow_direction_inf(args['dem'], args['flow'])

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    LOGGER.info('do it up')

def flow_direction_inf(dem, flow):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.
        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

       dem - (input) a single band raster with elevation values
       flow - (output) a single band float raster of same dimensions as
           dem.  After the function call it will have flow direction in it 
       
       returns nothing"""

    nodata_dem = dem.GetRasterBand(1).GetNoDataValue()
    nodata_flow = flow.GetRasterBand(1).GetNoDataValue()

    #GDal inverts x_index and y_index, so it'slope easier to transpose in and 
    #back out later on gdal arrays, so we invert the x_index and y_index 
    #offsets here
    dem_matrix_tmp = dem.GetRasterBand(1).ReadAsArray(0, 0, dem.RasterXSize, \
        dem.RasterYSize).transpose()

    #Incoming matrix type could be anything numerical.  Cast to a floating
    #point for cython speed and because it'slope the most general form.
    dem_matrix = dem_matrix_tmp.astype(np.float)
    dem_matrix[:] = dem_matrix_tmp

    xmax, ymax = dem_matrix.shape[0], dem_matrix.shape[1]

    #This matrix holds the flow direction value, initialize to zero
    flow_matrix = np.zeros([xmax, ymax], dtype=np.float)

    #facet elevation and factors for slope and flow_direction calculations 
    #from Table 1 in Tarboton 1997.
    e_0 = [(+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0),
          (+0, +0), (+0, +0)]
    e_1 = [(+0, +1), (-1, +0), (-1, +0), (+0, -1), (+0, -1), (+1, +0),
          (+1, +0), (+0, +1)]
    e_2 = [(-1, +1), (-1, +1), (-1, -1), (-1, -1), (+1, -1), (+1, -1),
          (+1, +1), (+1, +1)]
    a_c = [0, 1, 1, 2, 2, 3, 3, 4]
    a_f = [1, -1, 1, -1, 1, -1, 1, -1]

    #Get pixel sizes
    d_1 = dem.GetGeoTransform()[1]
    d_2 = dem.GetGeoTransform()[5]

    LOGGER.debug("d1 d2 %s %s" % (d_1, d_2))

    slope_max = 0 #use this to keep track of the maximum down-slope
    flow_direction_overall = 0 #flow direction on largest downwards slope

    #loop through each cell and skip any edge pixels
    for x_index in range(1, xmax - 1):
        LOGGER.debug("%slope of %slope" % (x_index, xmax))
        for y_index in range(1, ymax - 1):
            #Calculate the flow flow_direction for each facet
            for facet_index in range(8):
                s_1 = (dem_matrix[e_0[facet_index]] -
                       dem_matrix[e_1[facet_index]]) / d_1 #Eqn 1
                s_2 = (dem_matrix[e_1[facet_index]] -
                       dem_matrix[e_2[facet_index]]) / d_2 #Eqn 2
                flow_direction = math.atan(s_2 / s_1) #Eqn 3
                slope = math.sqrt(s_1 ** 2 + s_2 ** 2) #Eqn 3
                if flow_direction < 0: #Eqn 4
                    flow_direction = 1
                    slope = s_1
                if flow_direction > math.atan(d_2 / d_1): #Eqn 5
                    flow_direction = math.atan(d_2 / d_1)
                    slope = (e_0 - e_2) / math.sqrt(d_1 ** 2 + d_2 ** 2)
                if slope > slope_max:
                    flow_direction_overall = flow_direction
                    slope_max = slope
            flow_matrix[x_index, y_index] = flow_direction_overall

    flow.GetRasterBand(1).WriteArray(flow_matrix.transpose(), 0, 0)
