"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging

import scipy.sparse
import scipy.sparse.linalg
import numpy as np
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core
from invest_natcap import raster_utils

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
        args['flow_direction'] - An output raster indicating the flow direction
            on each pixel
        args['v_stream'] - An output raster indicating the areas that are
            classified as streams based on flow_direction
        args['sret_dr_uri'] - An output raster uri showing the amount of
            sediment retained on each pixel during routing.  It breaks
            convention to pass a URI here, but we won't know the shape of
            the raster until after all the input rasters are rasterized.
        args['sexp_dr_uri'] - An output raster uri showing the amount of
            sediment exported from each pixel during routing.  It breaks
            convention to pass a URI here, but we won't know the shape of
            the raster until after all the input rasters are rasterized.
            
        returns nothing"""

    ##############Set up vectorize functions and function-wide values
    LOGGER = logging.getLogger('sediment_core: biophysical')

    flow_accumulation_nodata = \
            args['flow_accumulation'].GetRasterBand(1).GetNoDataValue()
    v_stream_nodata = \
        args['v_stream'].GetRasterBand(1).GetNoDataValue()

    def stream_classifier(flow_accumulation):
        """This function classifies pixels into streams or no streams based
            on the threshold_flow_accumulation value.

            flow_accumulation - GIS definition of flow accumulation (upstream
                pixel inflow)

            returns 1 if flow_accumulation exceeds
                args['threshold_flow_accumulation'], 0 if not, and nodata
                if in a nodata region
        """
        if flow_accumulation == flow_accumulation_nodata:
            return v_stream_nodata
        if flow_accumulation >= args['threshold_flow_accumulation']:
            return 1.0
        else:
            return 0.0

    #Nodata value to use for usle output raster
    usle_nodata = -1.0
    usle_c_p_raster = raster_utils.new_raster_from_base(args['landuse'], '',
        'MEM', usle_nodata, gdal.GDT_Float32)
    def lulc_to_cp(lulc_code):
        """This is a helper function that's used to map an LULC code to the
            C * P values needed by the sediment model and defined
            in the biophysical table in the closure above.  The intent is this
            function is used in a vectorize operation for a single raster.
            
            lulc_code - an integer representing a LULC value in a raster
            
            returns C*P where C and P are defined in the 
                args['biophysical_table']
        """
        #There are string casts here because the biophysical table is all 
        #strings thanks to the csv table conversion.
        if str(lulc_code) not in args['biophysical_table']:
            return usle_nodata
        #We need to divide the c and p factors by 1000 (10*6 == 1000*1000) 
        #because they're stored in the table as C * 1000 and P * 1000.  See 
        #the user's guide:
        #http://ncp-dev.stanford.edu/~dataportal/invest-releases/documentation/2_2_0/sediment_retention.html
        return float(args['biophysical_table'][str(lulc_code)]['usle_c']) * \
            float(args['biophysical_table'][str(lulc_code)]['usle_p']) / \
                10 ** 6

    #Set up structures and functions for USLE calculation
    ls_nodata = args['ls_factor'].GetRasterBand(1).GetNoDataValue()
    erosivity_nodata = args['erosivity'].GetRasterBand(1).GetNoDataValue()
    erodibility_nodata = args['erodibility'].GetRasterBand(1).GetNoDataValue()

    def usle_function(ls_factor, erosivity, erodibility, usle_c_p, v_stream):
        """Calculates the USLE equation 
        
        ls_factor - length/slope factor
        erosivity - related to peak rainfall events
        erodibility - related to the potential for soil to erode
        usle_c_p - crop and practice factor which helps to abate soil erosion
        v_stream - 1 or 0 depending if there is a stream there.  If so, no
            potential soil loss due to USLE
        
        returns ls_factor * erosivity * erodibility * usle_c_p if all arguments
            defined, nodata if some are not defined, 0 if in a stream
            (v_stream)"""

        if ls_factor == usle_nodata or erosivity == usle_nodata or \
            erodibility == usle_nodata or usle_c_p == usle_nodata or \
            v_stream == v_stream_nodata:
            return usle_nodata
        if v_stream == 1:
            return 0
        return ls_factor * erosivity * erodibility * usle_c_p
    usle_vectorized_function = np.vectorize(usle_function)

    retention_efficiency_raster_raw = \
        raster_utils.new_raster_from_base(args['landuse'], '', 'MEM',
                                             usle_nodata, gdal.GDT_Float32)

    def lulc_to_retention(lulc_code):
        """This is a helper function that's used to map an LULC code to the
            retention values needed by the sediment model and defined
            in the biophysical table in the closure above.  The intent is this
            function is used in a vectorize operation for a single raster.
            
            lulc_code - an integer representing a LULC value in a raster
            
            returns C*P where C and P are defined in the 
                args['biophysical_table']
        """
        #There are string casts here because the biophysical table is all 
        #strings thanks to the csv table conversion.
        if str(lulc_code) not in args['biophysical_table']:
            return usle_nodata
        #We need to divide the retention efficiency by 100  because they're 
        #stored in the table as sedret_eff * 100.  See the user's guide:
        #http://ncp-dev.stanford.edu/~dataportal/invest-releases/documentation/2_2_0/sediment_retention.html
        return float(args['biophysical_table'] \
                     [str(lulc_code)]['sedret_eff']) / 100.0

    def efficiency_raster_creator(soil_loss, efficiency, v_stream):
        """Used for interpolating efficiency raster to be the same dimensions
            as soil_loss and also knocking out retention on the streams"""

        #v_stream is 1 in a stream 0 otherwise, so 1-v_stream can be used
        #to scale efficiency especially if v_steram is interpolated 
        #intelligently
        return (1 - v_stream) * efficiency

    ############## Calculation Starts here

    for watershed_feature in args['watersheds'].GetLayer():
        LOGGER.info('Working on watershed_feature %s' % watershed_feature.GetFID())
        watershed_bounding_box = \
            invest_core.bounding_box_index(watershed_feature, args['dem'])
        LOGGER.info('Bounding box %s' % (watershed_bounding_box))

        #Read the subraster that overlaps the watershed bounding box
        #dem_matrix = \
        #    args['dem'].GetRasterBand(1).ReadAsArray(watershed_bounding_box)
        LOGGER.info("calculating flow direction")
        invest_cython_core.flow_direction_inf(args['dem'],
                                              watershed_bounding_box,
                                              args['flow_direction'])

        LOGGER.info("calculating flow accumulation")
        invest_cython_core.flow_accumulation_dinf(args['flow_direction'],
                                                  args['dem'],
                                                  watershed_bounding_box,
                                                  args['flow_accumulation'])

        #classify streams from the flow accumulation raster
        LOGGER.info("Classifying streams from flow accumulation raster")
        invest_core.vectorize1ArgOp(args['flow_accumulation'].GetRasterBand(1),
            stream_classifier, args['v_stream'].GetRasterBand(1),
            watershed_bounding_box)

        LOGGER.info("Calculating slope")
        invest_cython_core.calculate_slope(args['dem'],
            watershed_bounding_box, args['slope'])

        LOGGER.info("calculating LS factor accumulation")
        invest_cython_core.calculate_ls_factor(args['flow_accumulation'],
                                               args['slope'],
                                               args['flow_direction'],
                                               watershed_bounding_box,
                                               args['ls_factor'])
        #map lulc to a usle_c * usle_p raster
        LOGGER.info('mapping landuse types to crop and practice management values')

        lulc_watershed_bounding_box = \
            invest_core.bounding_box_index(watershed_feature, args['landuse'])
        invest_core.vectorize1ArgOp(args['landuse'].GetRasterBand(1),
            lulc_to_cp, usle_c_p_raster.GetRasterBand(1),
            lulc_watershed_bounding_box)

        #map lulc to a usle_c * usle_p raster
        LOGGER.info('mapping landuse types to vegetation retention efficiencies')
        invest_core.vectorize1ArgOp(args['landuse'].GetRasterBand(1),
            lulc_to_retention,
            retention_efficiency_raster_raw.GetRasterBand(1),
            lulc_watershed_bounding_box)

    LOGGER.info("calculating potential soil loss")
    potential_soil_loss = invest_core.vectorizeRasters([args['ls_factor'],
        args['erosivity'], args['erodibility'], usle_c_p_raster,
        args['v_stream']], usle_vectorized_function, args['usle_uri'],
        nodata=usle_nodata)

    #change units from tons per hectare to tons per cell.  We need to do this
    #after the vectorize raster operation since we won't know the cell size
    #until then.  Convert cell_area to meters (in Ha by default)
    cell_area = invest_cython_core.pixelArea(potential_soil_loss) * (10 ** 4)
    LOGGER.debug("{cell_area: %s" % cell_area)
    potential_soil_loss_matrix = potential_soil_loss.GetRasterBand(1). \
        ReadAsArray(0, 0, potential_soil_loss.RasterXSize,
                    potential_soil_loss.RasterYSize)
    potential_soil_loss_nodata = \
        potential_soil_loss.GetRasterBand(1).GetNoDataValue()
    potential_soil_loss_nodata_mask = \
        potential_soil_loss_matrix == potential_soil_loss_nodata
    potential_soil_loss_matrix *= cell_area / 10000.0
    potential_soil_loss_matrix[potential_soil_loss_nodata_mask] = \
        potential_soil_loss_nodata
    #Get rid of any negative values due to outside interpolation:
    potential_soil_loss_matrix[potential_soil_loss_matrix < 0] = \
        potential_soil_loss_nodata
    potential_soil_loss.GetRasterBand(1). \
        WriteArray(potential_soil_loss_matrix, 0, 0)
    invest_core.calculateRasterStats(potential_soil_loss.GetRasterBand(1))

    sret_dr_raw = raster_utils.new_raster_from_base(potential_soil_loss,
        '', 'MEM', -1.0, gdal.GDT_Float32)

    #now interpolate retention_efficiency_raster_raw to a raster that will
    #overlay potential_soil_loss, bastardizing vectorizeRasters here for
    #its interpolative functionality by only returning efficiency in the
    #vectorized op.
    usle_vectorized_function = np.vectorize(efficiency_raster_creator)
    retention_efficiency_raster = \
        invest_core.vectorizeRasters([potential_soil_loss,
            retention_efficiency_raster_raw, args['v_stream']],
            usle_vectorized_function, nodata=usle_nodata)

    #Create an output raster for routed sediment retention
    sret_dr = raster_utils.new_raster_from_base(potential_soil_loss,
        args['sret_dr_uri'], 'GTiff', -1.0, gdal.GDT_Float32)

    #Route the sediment across the landscape and store the amount retained
    #per pixel
    invest_cython_core.calc_retained_sediment(potential_soil_loss,
        args['flow_direction'], retention_efficiency_raster, sret_dr)

    #Create an output raster for routed sediment export
    sexp_dr = raster_utils.new_raster_from_base(potential_soil_loss,
        args['sexp_dr_uri'], 'GTiff', -1.0, gdal.GDT_Float32)
    invest_cython_core.calc_exported_sediment(potential_soil_loss,
        args['flow_direction'], retention_efficiency_raster,
        args['flow_accumulation'], args['v_stream'], sexp_dr)

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    LOGGER.info('not implemented yet')

def effective_retention(flow_direction_dataset, retention_efficiency_dataset,
                        effective_retention_uri):
    """Creates a raster of accumulated flow to each cell.
    
        flow_direction_dataset - (input) A raster showing direction of flow out 
            of each cell with directional values given in radians.
        retention_efficiency_dataset - (input) raster indicating percent of 
            sediment retained per pixel.  Streams are indicated by retention 
            efficiency of 0.
        effective_retention_uri - (input) The URI to the output dataset
        
        returns a dataset whose pixel values indicate the effective retention to
            stream"""


    effective_retention_dataset = raster_utils.new_raster_from_base(flow_direction_dataset, 
        effective_retention_uri, 'GTiff', -1.0, gdal.GDT_Float32)
    effective_retention_band = effective_retention_dataset.GetRasterBand(1)
    effective_retention_band.Fill(-1.0)

    flow_direction_band = flow_direction_dataset.GetRasterBand(1)
    flow_direction_nodata = flow_direction_band.GetNoDataValue()
    flow_direction_array = flow_direction_band.ReadAsArray().flatten()

    retention_efficiency_band = retention_efficiency_dataset.GetRasterBand(1)
    retention_efficiency_nodata = retention_efficiency_band.GetNoDataValue()
    retention_efficiency_array = \
        retention_efficiency_band.ReadAsArray().flatten()

    n_rows = effective_retention_dataset.RasterYSize
    n_cols = effective_retention_dataset.RasterXSize

    def calc_index(i, j):
        """used to abstract the 2D to 1D index calculation below"""
        if i >= 0 and i < n_rows and j >= 0 and j < n_cols:
            return i * n_cols + j
        else:
            return -1

    #set up variables to hold the sparse system of equations
    #upper bound  n*m*5 elements
    b_vector = np.zeros(n_rows * n_cols)

    #holds the rows for diagonal sparse matrix creation later, row 4 is 
    #the diagonal
    a_matrix = np.zeros((9, n_rows * n_cols))
    diags = np.array([-n_cols-1, -n_cols, -n_cols+1, -1, 0, 
                       1, n_cols-1, n_cols, n_cols+1])
    
    #Determine the outflow directions based on index offsets.  It's written 
    #in terms of radian 4ths for easier readability and maintaince. 
    #Derived all this crap from page 36 in Rich's notes.
    inflow_directions = {( 0, 1): (0.0/4.0 * np.pi, 5, False),
                         (-1, 1): (1.0/4.0 * np.pi, 2, True),
                         (-1, 0): (2.0/4.0 * np.pi, 1, False),
                         (-1,-1): (3.0/4.0 * np.pi, 0, True),
                         ( 0,-1): (4.0/4.0 * np.pi, 3, False),
                         ( 1,-1): (5.0/4.0 * np.pi, 6, True),
                         ( 1, 0): (6.0/4.0 * np.pi, 7, False),
                         ( 1, 1): (7.0/4.0 * np.pi, 8, True)}

    LOGGER.info('Building diagonals for linear advection diffusion system.')
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            #diagonal element row_index,j always in bounds, calculate directly
            cell_index = calc_index(row_index, col_index)
            a_matrix[4, cell_index] = 1
            
            #Check to see if the current flow angle is defined, if not then
            #set local flow accumulation to 0
            local_flow_angle = flow_direction_array[cell_index]
            if local_flow_angle == flow_direction_nodata:
                #b_vector already == 0 at this point, so just continue
                continue

            #Determine outflow neighbors
            sink = True
            for (row_offset, col_offset), (outflow_angle, diagonal_offset, diagonal_outflow) in \
                    inflow_directions.iteritems():
                try:
                    neighbor_index = calc_index(row_index+row_offset,
                                                col_index+col_offset)
                    flow_angle = flow_direction_array[neighbor_index]

                    if flow_angle == flow_direction_nodata:
                        continue

                    #If this delta is within pi/4 it means there's an outflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(flow_angle - outflow_angle)

                    if delta < np.pi/4.0 or (2*np.pi - delta) < np.pi/4.0:

                        neighbor_retention = retention_efficiency_array[neighbor_index]

                        if neighbor_retention == retention_efficiency_nodata:
                            continue

                        if diagonal_outflow:
                            #We want to measure the far side of the unit triangle
                            #so we measure that angle UP from theta = 0 on a unit
                            #circle
                            delta = np.pi/4-delta

                        #Taking absolute value because it might be on a 0,-45 
                        #degree angle
                        outflow_fraction = abs(np.tan(delta))
                        if not diagonal_outflow:
                            #If not diagonal then we measure the direct flow in
                            #which is the inverse of the tangent function
                            outflow_fraction = 1-outflow_fraction
                        
                        #Finally set the appropriate inflow variable
                        a_matrix[diagonal_offset, neighbor_index] = \
                            -outflow_fraction * (1.0-neighbor_retention)
                        sink = False

                except IndexError:
                    #This will occur if we visit a neighbor out of bounds
                    #it's okay, just skip it
                    pass
                #A sink will have 100% export (to stream)
                b_vector[cell_index] = 1.0

    matrix = scipy.sparse.spdiags(a_matrix, diags, n_rows * n_cols, n_rows * n_cols, 
                                  format="csc")

    LOGGER.info('Solving via sparse direct solver')
    solver = scipy.sparse.linalg.factorized(matrix)
    result = solver(b_vector)

    #Result is a 1D array of all values, put it back to 2D
    result.resize(n_rows,n_cols)

    effective_retention_band.WriteArray(result)

    return effective_retention_dataset
