"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import bisect
import os

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
        args['slope_uri'] - an output raster file that holds the slope percentage
            as a proporition from the dem
        args['ls_uri'] - an output path for the ls_factor calculated on the 
            particular dem
        args['v_stream_uri'] - A path to a  file that classifies the
            watersheds into stream and non-stream regions based on the
            value of 'threshold_flow_accumulation'
        args['flow_direction'] - An output raster indicating the flow direction
            on each pixel
        args['sret_dr_uri'] - An output raster uri showing the amount of
            sediment retained on each pixel during routing.  It breaks
            convention to pass a URI here, but we won't know the shape of
            the raster until after all the input rasters are rasterized.
        args['sexp_dr_uri'] - An output raster uri showing the amount of
            sediment exported from each pixel during routing.  It breaks
            convention to pass a URI here, but we won't know the shape of
            the raster until after all the input rasters are rasterized.
        args['intermediate_uri'] - A path to store itermediate rasters
        args['output_uri'] - A path to store output rasters
        returns nothing"""

    ##############Set up vectorize functions and function-wide values
    LOGGER = logging.getLogger('sediment_core: biophysical')

    flow_accumulation_nodata = \
            args['flow_accumulation'].GetRasterBand(1).GetNoDataValue()
    v_stream_nodata = \
        args['v_stream'].GetRasterBand(1).GetNoDataValue()

    #Nodata value to use for usle output raster
    usle_nodata = -1.0

    #Set up structures and functions for USLE calculation
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

    def efficiency_raster_creator(soil_loss, efficiency, v_stream):
        """Used for interpolating efficiency raster to be the same dimensions
            as soil_loss and also knocking out retention on the streams"""

        #v_stream is 1 in a stream 0 otherwise, so 1-v_stream can be used
        #to scale efficiency especially if v_steram is interpolated 
        #intelligently
        return (1 - v_stream) * efficiency

    ############## Calculation Starts here

    dem_dataset = args['dem']
    n_rows = dem_dataset.RasterYSize
    n_cols = dem_dataset.RasterXSize
    
    #Calculate flow
    LOGGER.info("calculating flow direction")
    bounding_box = [0, 0, n_cols, n_rows]
    invest_cython_core.flow_direction_inf(dem_dataset, bounding_box, 
        args['flow_direction'])

    #Calculate slope
    LOGGER.info("Calculating slope")
    slope_dataset = raster_utils.calculate_slope(dem_dataset, args['slope_uri'])

    #Calcualte flow accumulation
    LOGGER.info("calculating flow accumulation")
    invest_cython_core.flow_accumulation_dinf(args['flow_direction'],
        args['dem'], bounding_box, args['flow_accumulation'])

    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    stream_dataset = raster_utils.stream_threshold(args['flow_accumulation'], 
        args['threshold_flow_accumulation'], args['v_stream_uri'])

    #Calculate LS term
    ls_dataset = calculate_ls_factor(args['flow_accumulation'], slope_dataset, 
                                     args['flow_direction'], args['ls_uri'])


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

    retention_uri = os.path.join(args['intermediate_uri'],'retention.tif')
    raster_utils.vectorize_rasters([args['landuse']], lulc_to_retention, 
                                   raster_out_uri = retention_uri, 
                                   datatype=gdal.GDT_Float32, nodata=-1.0)


    def lulc_to_c_or_p(key, lulc_code):
        """This is a helper function that's used to map an LULC code to the
            C * P values needed by the sediment model and defined
            in the biophysical table in the closure above.  The intent is this
            function is used in a vectorize operation for a single raster.
            
            key - either 'usle_c' or 'usle_p'
            lulc_code - an integer representing a LULC value in a raster
            
            returns C or P where C and P are defined in the 
                args['biophysical_table']
        """
        #There are string casts here because the biophysical table is all 
        #strings thanks to the csv table conversion.
        if str(lulc_code) not in args['biophysical_table']:
            return usle_nodata
        #We need to divide the c and p factors by 1000
        #because they're stored in the table as C * 1000 and P * 1000.  See 
        #the user's guide:
        #http://ncp-dev.stanford.edu/~dataportal/invest-releases/documentation/2_2_0/sediment_retention.html
        return float(args['biophysical_table'][str(lulc_code)][key]) / 1000.0

    c_factor_uri = os.path.join(args['intermediate_uri'],'c_factor.tif')
    p_factor_uri = os.path.join(args['intermediate_uri'],'p_factor.tif')
    c_dataset = raster_utils.vectorize_rasters([args['landuse']], 
                                   lambda x: lulc_to_c_or_p('usle_c',x), 
                                   raster_out_uri = c_factor_uri, 
                                   datatype=gdal.GDT_Float32, nodata=-1.0)
    p_dataset = raster_utils.vectorize_rasters([args['landuse']], 
                                   lambda x: lulc_to_c_or_p('usle_p',x), 
                                   raster_out_uri = p_factor_uri, 
                                   datatype=gdal.GDT_Float32, nodata=-1.0)

    potential_sediment_export_dataset = \
       calculate_potential_soil_loss(ls_dataset, \
                args['erosivity'], args['erodibility'], c_dataset, p_dataset,\
                stream_dataset, args['usle_uri'])

    effective_retention_uri = os.path.join(args['intermediate_uri'], 
                                           'effective_retention.tif')

    retention_efficiency_uri = \
        os.path.join(args['intermediate_uri'],'sed_ret_eff.tif')
    retention_efficiency_dataset = \
        raster_utils.vectorize_rasters([args['landuse']], lulc_to_retention, 
            raster_out_uri = retention_efficiency_uri, 
            datatype = gdal.GDT_Float32, nodata = -1.0)

    effective_retention_dataset = \
        effective_retention(args['flow_direction'], \
            retention_efficiency_dataset, stream_dataset, 
            effective_retention_uri)

    pixel_export_uri = os.path.join(args['output_uri'], 'pixel_export.tif')
    calculate_per_pixel_export(potential_sediment_export_dataset,
        effective_retention_dataset, pixel_export_uri)

    pixel_sediment_flow_uri = \
        os.path.join(args['intermediate_uri'], 'pixel_sed_flow.tif')
    pixel_sediment_core_dataset = \
        pixel_sediment_flow(potential_sediment_export_dataset, \
            args['flow_direction'], effective_retention_dataset, 
            pixel_sediment_flow_uri)

    sediment_retained_uri = \
        os.path.join(args['output_uri'], 'pixel_retained.tif')
    calculate_pixel_retained(pixel_sediment_core_dataset,
        effective_retention_dataset, args['flow_direction'], 
        sediment_retained_uri)

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    LOGGER.info('not implemented yet')

def effective_retention(flow_direction_dataset, retention_efficiency_dataset,
                        stream_dataset, effective_retention_uri):
    """Creates a raster of accumulated flow to each cell.
    
        flow_direction_dataset - (input) A raster showing direction of flow out 
            of each cell with directional values given in radians.
        retention_efficiency_dataset - (input) raster indicating percent of 
            sediment retained per pixel.  
        stream_dataset - (input) raster indicating the presence (1) or absence
            (0) of a stream.
        effective_retention_uri - (input) The URI to the output dataset
        
        returns a dataset whose pixel values indicate the effective retention to
            stream"""

    effective_retention_nodata = -1.0
    effective_retention_dataset = \
        raster_utils.new_raster_from_base(flow_direction_dataset,
            effective_retention_uri, 'GTiff', effective_retention_nodata, 
            gdal.GDT_Float32)

    effective_retention_band = effective_retention_dataset.GetRasterBand(1)
    effective_retention_band.Fill(effective_retention_nodata)

    flow_direction_band, flow_direction_nodata = \
        raster_utils.extract_band_and_nodata(flow_direction_dataset)
    flow_direction_array = flow_direction_band.ReadAsArray().flatten()

    retention_efficiency_band, retention_efficiency_nodata = \
        raster_utils.extract_band_and_nodata(retention_efficiency_dataset)
    retention_efficiency_array = \
        retention_efficiency_band.ReadAsArray().flatten()

    stream_band, stream_nodata = \
        raster_utils.extract_band_and_nodata(stream_dataset)
    stream_array = stream_band.ReadAsArray().flatten()

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
    outflow_directions = {( 0, 1): (0.0/4.0 * np.pi, 5, False),
                          (-1, 1): (1.0/4.0 * np.pi, 2, True),
                          (-1, 0): (2.0/4.0 * np.pi, 1, False),
                          (-1,-1): (3.0/4.0 * np.pi, 0, True),
                          ( 0,-1): (4.0/4.0 * np.pi, 3, False),
                          ( 1,-1): (5.0/4.0 * np.pi, 6, True),
                          ( 1, 0): (6.0/4.0 * np.pi, 7, False),
                          ( 1, 1): (7.0/4.0 * np.pi, 8, True)}

    LOGGER.info('Building diagonals for effective retention system.')
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            #diagonal element row_index,j always in bounds, calculate directly
            cell_index = calc_index(row_index, col_index)
            a_matrix[4, cell_index] = 1
            
            if stream_array[cell_index] == 1.0:
                #We're in a stream
                b_vector[cell_index] = 1.0
                continue

            #Check to see if the current flow angle is defined, if not then
            #set local flow accumulation to 0
            local_flow_angle = flow_direction_array[cell_index]
            if local_flow_angle == flow_direction_nodata:
                #It's purely a nodata value
                b_vector[cell_index] = effective_retention_nodata
                continue

            #Determine outflow neighbors
            sink = True
            total_fraction = 0.0
            fraction_count = 0
            for flow_coords, flow_properties in outflow_directions.iteritems():
                try:
                    row_offset, col_offset = flow_coords
                    outflow_angle, diagonal_offset, diagonal_outflow = \
                        flow_properties

                    neighbor_index = calc_index(row_index+row_offset,
                                                col_index+col_offset)

                    #If this delta is within pi/4 it means there's an outflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(local_flow_angle - outflow_angle)

                    if delta < np.pi/4.0 or (2*np.pi - delta) < np.pi/4.0:
                        neighbor_retention = \
                            retention_efficiency_array[neighbor_index]

                        if neighbor_retention == retention_efficiency_nodata:
                            continue

                        if diagonal_outflow:
                            #We want to measure the far side of the unit 
                            #triangle so we measure that angle UP from 
                            #theta = 0 on a unit circle
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
                        total_fraction += outflow_fraction
                        fraction_count += 1

                except IndexError:
                    #This will occur if we visit a neighbor out of bounds
                    #it's okay, just skip it
                    pass

            #A sink will have 100% export (to stream)
            if sink:
                b_vector[cell_index] = 0.0

    n_elements = n_rows * n_cols
    matrix = scipy.sparse.spdiags(a_matrix, diags, n_elements, n_elements, 
                                  format="csc")

    LOGGER.info('Solving via sparse direct solver')
    solver = scipy.sparse.linalg.factorized(matrix)
    result = solver(b_vector)

    #Result is a 1D array of all values, put it back to 2D
    result.resize(n_rows, n_cols)

    effective_retention_band.WriteArray(result)

    return effective_retention_dataset

def calculate_ls_factor(flow_accumulation_dataset, slope_dataset, 
                        aspect_dataset, ls_factor_uri):
    """Calculates the LS factor as Equation 3 from "Extension and validation 
        of a geographic information system-based method for calculating the
        Revised Universal Soil Loss Equation length-slope factor for erosion
        risk assessments in large watersheds"   
        
        (Required that all raster inputs are same dimensions and projections
        and have square cells)
        flow_accumulation_dataset - a single band raster of type float that 
            indicates the contributing area at the inlet of a grid cell
        slope_dataset - a single band raster of type float that indicates
            the slope at a pixel given as a proportion (e.g. a value of 0.05
            is a slope of 5%)
        aspect_dataset - a single band raster of type float that indicates the 
            direction that slopes are facing in terms of radians east and
            increase clockwise: pi/2 is north, pi is west, 3pi/2, south and 
            0 or 2pi is east.
        ls_factor_uri - (input) a string to the path where the LS raster will 
            be written 
            
        returns a GDAL dataset that is the ls_raster as the same dimensions as 
            inputs"""
    
    #Tease out all the nodata values for reading and setting
    flow_accumulation_band = flow_accumulation_dataset.GetRasterBand(1)
    flow_accumulation_nodata = flow_accumulation_band.GetNoDataValue()
    flow_accumulation_matrix = flow_accumulation_band.ReadAsArray()

    slope_band = slope_dataset.GetRasterBand(1)
    slope_nodata = slope_band.GetNoDataValue()
    slope_matrix = slope_band.ReadAsArray()

    aspect_band = aspect_dataset.GetRasterBand(1)
    aspect_nodata = aspect_band.GetNoDataValue()
    aspect_matrix = aspect_band.ReadAsArray()

    #Assumes that cells are square
    cell_size = abs(flow_accumulation_dataset.GetGeoTransform()[1])
    cell_area = cell_size ** 2

    ls_nodata = -1.0

    def ls_factor_function(aspect, slope, flow_accumulation, aspect_angle):
        #Skip the calculation if any of the inputs are nodata
        if aspect == aspect_nodata or slope == slope_nodata or \
                flow_accumulation == flow_accumulation_nodata:
            return ls_nodata

        #Here the aspect direciton can range from 0 to 2PI, but the purpose
        #of the term is to determine the length of the flow path on the
        #pixel, thus we take the absolute value of each trigometric
        #function to keep the computation in the first quadrant
        xij = abs(np.sin(aspect_angle))+ abs(np.cos(aspect_angle))
            
        contributing_area = (flow_accumulation-1) * cell_area

        #A placeholder for simplified slope stuff
        slope_in_radians = np.arctan(slope)
            
        #From Equation 4 in "Extension and validataion of a geographic 
        #information system ..."
        if slope < 0.09:
            slope_factor =  10.8*np.sin(slope_in_radians)+0.03
        else:
            slope_factor =  16.8*np.sin(slope_in_radians)-0.5
            
        #Set the m value to the lookup table that's from Yonas's handwritten
        #notes.  On the margin it says "Equation 15".  Don't know from
        #where.
        beta = (np.sin(slope_in_radians) / 0.0896) / \
            (3*pow(np.sin(slope_in_radians),0.8)+0.56)
        slope_table = [0.01, 0.035, 0.05, 0.09]
        exponent_table = [0.2, 0.3, 0.4, 0.5, beta/(1+beta)]
            
        #Use the bisect function to do a nifty range 
        #lookup. http://docs.python.org/library/bisect.html#other-examples
        m = exponent_table[bisect.bisect(slope_table,slope)]

        #Use the bisect function to do a nifty range 
        #lookup. http://docs.python.org/library/bisect.html#other-examples
        m = exponent_table[bisect.bisect(slope_table,slope)]
        #The length part of the ls_factor:
        ls_factor = ((contributing_area+cell_area)**(m+1)- \
                         contributing_area**(m+1)) / \
                         ((cell_size**(m+2))*(xij**m)*(22.13**m))
                
        #From the paper "as a final check against exessively long slope
        #length calculations ... cap of 333m"
        if ls_factor > 333:
            ls_factor = 333
                
        return ls_factor * slope_factor


    #Call vectorize rasters for ls_factor
    dataset_list = [aspect_dataset, slope_dataset, flow_accumulation_dataset, 
                    aspect_dataset]
    ls_factor_dataset = \
        raster_utils.vectorize_rasters(dataset_list, ls_factor_function, \
                                       raster_out_uri=ls_factor_uri,\
                                       datatype=gdal.GDT_Float32, \
                                       nodata=ls_nodata)

    raster_utils.calculate_raster_stats(ls_factor_dataset)
    return ls_factor_dataset

def calculate_potential_soil_loss(ls_factor_dataset, erosivity_dataset, 
                                  erodibility_dataset, c_dataset, p_dataset,
                                  stream_dataset, usle_uri):

    """Calculates per-pixel potential soil loss using the RUSLE (revised 
        universial soil loss equation).

        ls_factor_dataset - GDAL dataset with the LS factor pre-calculated
        erosivity_dataset - GDAL dataset with per pixel erosivity 
        erodibility_dataset - GDAL dataset with per pixel erodibility
        c_dataset - GDAL dataset per pixel crop managment factor
        p_dataset - GDAL dataset per pixel land management factor
        stream_dataset - GDAL dataset indicating locations with streams
            (0 is no stream, 1 stream)
        usle_uri - string input indicating the path to disk
            for the resulting potential soil loss raster

        return GDAL dataset with potential per pixel soil loss"""


    ls_factor_nodata = ls_factor_dataset.GetRasterBand(1).GetNoDataValue()
    erosivity_nodata = erosivity_dataset.GetRasterBand(1).GetNoDataValue()
    erodibility_nodata = erodibility_dataset.GetRasterBand(1).GetNoDataValue()
    c_nodata = c_dataset.GetRasterBand(1).GetNoDataValue()
    p_nodata = p_dataset.GetRasterBand(1).GetNoDataValue()
    stream_nodata = stream_dataset.GetRasterBand(1).GetNoDataValue()

    usle_nodata = -1.0
    ls_factor_nodata = -1.0
    def usle_function(ls_factor, erosivity, erodibility, usle_c, usle_p, 
                      v_stream):
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

        if ls_factor == ls_factor_nodata or erosivity == erosivity_nodata or \
            erodibility == erodibility_nodata or usle_c == c_nodata or \
            usle_p == p_nodata or v_stream == stream_nodata:
            return usle_nodata
        if v_stream == 1:
            return 0.0
        return ls_factor * erosivity * erodibility * usle_c * usle_p

    dataset_list = [ls_factor_dataset, erosivity_dataset, erodibility_dataset, 
                    c_dataset, p_dataset, stream_dataset]

    potential_soil_loss_dataset = raster_utils.vectorize_rasters(dataset_list,
        usle_function, raster_out_uri = usle_uri, 
        datatype=gdal.GDT_Float32, nodata = usle_nodata)


    #change units from tons per hectare to tons per cell.  We need to do this
    #after the vectorize raster operation since we won't know the cell size
    #until then.
    cell_area = raster_utils.pixel_area(potential_soil_loss_dataset)

    potential_soil_loss_band = potential_soil_loss_dataset.GetRasterBand(1)
    potential_soil_loss_matrix = potential_soil_loss_band.ReadAsArray()
    potential_soil_loss_nodata = potential_soil_loss_band.GetNoDataValue()
    potential_soil_loss_data_mask = \
        potential_soil_loss_matrix != potential_soil_loss_nodata

    #current unit is tons/ha, multiply by ha/cell (cell area in m^2/100**2)
    potential_soil_loss_matrix[potential_soil_loss_data_mask] *= \
        cell_area / 10000.0

    potential_soil_loss_band.WriteArray(potential_soil_loss_matrix)
    raster_utils.calculate_raster_stats(potential_soil_loss_dataset)

    return potential_soil_loss_dataset

def calculate_per_pixel_export(potential_sediment_loss_dataset, 
                     effective_retention_dataset, pixel_export_uri):
    """Calculate per pixel export based on potential soil loss and the 
        effective per pixel retention factor.

        potential_sediment_loss_dataset - a gdal dataset with per pixel 
            potential export in units of tons per pixel
        effective_retention_dataset - a gdal dataset whose values indicate
            the amount of potential export from a particular pixel to 
            the stream
        pixel_export_uri - the path to disk for the output raster

        returns a dataset that has effective per pixel export to stream"""

    pixel_export_nodata = -1.0

    potential_sediment_loss_band, potential_sediment_loss_nodata = \
        raster_utils.extract_band_and_nodata(potential_sediment_loss_dataset)

    effective_retention_band, effective_retention_nodata = \
        raster_utils.extract_band_and_nodata(effective_retention_dataset)

    def pixel_export_op(potential_sediment_loss, retention):
        """This either returns nodata in undefined areas or multplies the
            sediment export by the effective retention"""
        if potential_sediment_loss == potential_sediment_loss_nodata or \
                retention == effective_retention_nodata:
            return pixel_export_nodata
        return potential_sediment_loss * retention

    #Still call vectorize rasters for memory and/or interpolation reasons.
    pixel_export_dataset = \
        raster_utils.vectorize_rasters([potential_sediment_loss_dataset, \
        effective_retention_dataset], pixel_export_op, \
        datatype = gdal.GDT_Float32, nodata = pixel_export_nodata, \
        raster_out_uri = pixel_export_uri)

    return pixel_export_dataset

def pixel_sediment_flow(potential_sediment_loss_dataset, flow_direction_dataset,
                        retention_efficiency_dataset, pixel_sediment_flow_uri):
    """Creates a raster of total sediment outflow from each pixel.
    
        potential_sediment_loss_dataset - a gdal dataset with per pixel 
            potential export in units of tons per pixel
        flow_direction_dataset - (input) A raster showing direction of flow out 
            of each cell with directional values given in radians.
        retention_efficiency_dataset - (input) raster indicating percent of 
            sediment retained per pixel.  
        pixel_sediment_flow_uri - (input) The URI to the output dataset

        returns a dataset that has an amount of sediment in tons outflowing
            from each pixel"""

    potential_sediment_loss_band, potential_sediment_loss_nodata = \
        raster_utils.extract_band_and_nodata(potential_sediment_loss_dataset)
    potential_sediment_loss_array = \
        potential_sediment_loss_band.ReadAsArray().flatten()

    flow_direction_band, flow_direction_nodata = \
        raster_utils.extract_band_and_nodata(flow_direction_dataset)
    flow_direction_array = flow_direction_band.ReadAsArray().flatten()

    retention_efficiency_band, retention_efficiency_nodata = \
        raster_utils.extract_band_and_nodata(retention_efficiency_dataset)
    retention_efficiency_array = \
        retention_efficiency_band.ReadAsArray().flatten()

    pixel_sediment_flow_nodata = -1.0
    pixel_sediment_flow_dataset = \
        raster_utils.new_raster_from_base(flow_direction_dataset, 
            pixel_sediment_flow_uri, 'GTiff', pixel_sediment_flow_nodata, 
            gdal.GDT_Float32)

    pixel_sediment_flow_band = pixel_sediment_flow_dataset.GetRasterBand(1)
    pixel_sediment_flow_band.Fill(pixel_sediment_flow_nodata)

    n_rows = pixel_sediment_flow_dataset.RasterYSize
    n_cols = pixel_sediment_flow_dataset.RasterXSize

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
    inflow_directions = {( 0, 1): (4.0/4.0 * np.pi, 5, False),
                         (-1, 1): (5.0/4.0 * np.pi, 2, True),
                         (-1, 0): (6.0/4.0 * np.pi, 1, False),
                         (-1,-1): (7.0/4.0 * np.pi, 0, True),
                         ( 0,-1): (0.0/4.0 * np.pi, 3, False),
                         ( 1,-1): (1.0/4.0 * np.pi, 6, True),
                         ( 1, 0): (2.0/4.0 * np.pi, 7, False),
                         ( 1, 1): (3.0/4.0 * np.pi, 8, True)}

    LOGGER.info('Building diagonals for linear advection diffusion system.')
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            #diagonal element row_index,j always in bounds, calculate directly
            cell_index = calc_index(row_index, col_index)
            a_matrix[4, cell_index] = 1
            
            #Check to see if the current flow angle is defined, if not then
            #set local flow accumulation to 0
            local_flow_angle = flow_direction_array[cell_index]
            local_retention = retention_efficiency_array[cell_index]
            local_sediment_loss = potential_sediment_loss_array[cell_index]

            if local_sediment_loss == potential_sediment_loss_nodata or \
                    local_retention == retention_efficiency_nodata or \
                    local_flow_angle == flow_direction_nodata:
                #if the local sediment is undefined we're gonna have a bad time
                #set to nodata value
                b_vector[cell_index] = pixel_sediment_flow_nodata

            b_vector[cell_index] = local_sediment_loss

            #Determine inflow neighbors
            for flow_coords, flow_properties in inflow_directions.iteritems():
                try:
                    row_offset, col_offset = flow_coords
                    inflow_angle, diagonal_offset, diagonal_inflow = \
                        flow_properties
                    neighbor_index = calc_index(row_index+row_offset,
                                                col_index+col_offset)

                    #If this delta is within pi/4 it means there's an inflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(local_flow_angle - inflow_angle)

                    if delta < np.pi/4.0 or (2*np.pi - delta) < np.pi/4.0:
                        neighbor_retention = \
                            retention_efficiency_array[neighbor_index]
                        neighbor_sediment_loss = \
                            potential_sediment_loss_array[neighbor_index]

                        if neighbor_retention == retention_efficiency_nodata or \
                                neighbor_sediment_loss == potential_sediment_loss_nodata:
                            continue

                        if diagonal_inflow:
                            #We want to measure the far side of the unit 
                            #triangle so we measure that angle UP from 
                            #theta = 0 on a unit circle
                            delta = np.pi/4-delta

                        #Taking absolute value because it might be on a 0,-45
                        #degree angle
                        inflow_fraction = abs(np.tan(delta))
                        if not diagonal_inflow:
                            #If not diagonal then we measure the direct flow in
                            #which is the inverse of the tangent function
                            inflow_fraction = 1-inflow_fraction
                        
                        #Finally set the appropriate inflow variable
                        a_matrix[diagonal_offset, neighbor_index] = \
                            -inflow_fraction * local_retention

                except IndexError:
                    #This will occur if we visit a neighbor out of bounds
                    #it's okay, just skip it
                    pass

    matrix = scipy.sparse.spdiags(a_matrix, diags, n_rows * n_cols, n_rows * n_cols, 
                                  format="csc")

    LOGGER.info('Solving via sparse direct solver')
    solver = scipy.sparse.linalg.factorized(matrix)
    result = solver(b_vector)

    #Result is a 1D array of all values, put it back to 2D
    result.resize(n_rows,n_cols)

    pixel_sediment_flow_band.WriteArray(result)

    return pixel_sediment_flow_dataset

def calculate_pixel_retained(pixel_sediment_flow_dataset, 
                             retention_efficiency_dataset,
                             flow_direction_dataset,
                             per_pixel_retained_uri):
    """Creates a raster of total sediment retention in each pixel.
    
        pixel_sediment_flow_dataset - a gdal dataset with per pixel 
            sediment outflow
        retention_efficiency_dataset - (input) raster indicating percent of 
            sediment retained per pixel.  
        flow_direction_dataset - A raster showing direction of flow out 
            of each cell with directional values given in radians.
        pixel_retained_uri - The URI to the output dataset

        returns a dataset that has an amount of sediment in tons outflowing
            from each pixel"""


    pixel_sediment_flow_band, pixel_sediment_flow_nodata = \
        raster_utils.extract_band_and_nodata(pixel_sediment_flow_dataset)
    pixel_sediment_flow_array = pixel_sediment_flow_band.ReadAsArray().flatten()

    retention_efficiency_band, retention_efficiency_nodata = \
        raster_utils.extract_band_and_nodata(retention_efficiency_dataset)
    retention_efficiency_array = \
        retention_efficiency_band.ReadAsArray().flatten()

    flow_band, flow_nodata = \
        raster_utils.extract_band_and_nodata(flow_dataset)
    flow_array = flow_band.ReadAsArray().flatten()

    pixel_retained_nodata = -1.0
    pixel_retained_dataset = \
        raster_utils.new_raster_from_base(pixel_sediment_flow_dataset, 
        per_pixel_retained_uri, 'GTiff', pixel_retained_nodata, 
        gdal.GDT_Float32)
    pixel_retained_band = pixel_retained_dataset.GetRasterBand(1)
    pixel_retained_band.Fill(pixel_retained_nodata)

    n_rows = pixel_retained_dataset.RasterYSize
    n_cols = pixel_retained_dataset.RasterXSize

    def calc_index(i, j):
        """used to abstract the 2D to 1D index calculation below"""
        if i >= 0 and i < n_rows and j >= 0 and j < n_cols:
            return i * n_cols + j
        else:
            return -1

    result = np.zeros(n_rows*n_cols)

    #Determine the outflow directions based on index offsets.  It's written 
    #in terms of radian 4ths for easier readability and maintaince. 
    #Derived all this crap from page 36 in Rich's notes.
    inflow_directions = {( 0, 1): (4.0/4.0 * np.pi, 5, False),
                         (-1, 1): (5.0/4.0 * np.pi, 2, True),
                         (-1, 0): (6.0/4.0 * np.pi, 1, False),
                         (-1,-1): (7.0/4.0 * np.pi, 0, True),
                         ( 0,-1): (0.0/4.0 * np.pi, 3, False),
                         ( 1,-1): (1.0/4.0 * np.pi, 6, True),
                         ( 1, 0): (2.0/4.0 * np.pi, 7, False),
                         ( 1, 1): (3.0/4.0 * np.pi, 8, True)}

    LOGGER.info('Building diagonals for linear advection diffusion system.')
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            #diagonal element row_index,j always in bounds, calculate directly
            cell_index = calc_index(row_index, col_index)
            
            #Check to see if the current flow angle is defined, if not then
            #set local flow accumulation to 0
            local_flow_angle = flow_direction_array[cell_index]
            local_retention = retention_efficiency_array[cell_index]
            local_sediment_flow = pixel_sediment_flow_array[cell_index]

            if local_sediment_flow == pixel_sediment_flow_nodata or \
                    local_retention == retention_efficiency_nodata or \
                    local_flow_angle == flow_direction_nodata:
                #if the local sediment is undefined we're gonna have a bad time
                #set to nodata value
                result[cell_index] = pixel_retained_nodata
                continue

            #Determine inflow neighbors

            for flow_coords, flow_properties in inflow_directions.iteritems():
                try:
                    row_offset, col_offset = flow_coords
                    inflow_angle, diagonal_offset, diagonal_inflow = \
                        flow_properties
                    neighbor_index = calc_index(row_index+row_offset,
                                                col_index+col_offset)

                    #If this delta is within pi/4 it means there's an inflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(local_flow_angle - inflow_angle)

                    if delta < np.pi/4.0 or (2*np.pi - delta) < np.pi/4.0:
                        neighbor_retention = \
                            retention_efficiency_array[neighbor_index]
                        if neighbor_retention == retention_efficiency_nodata:
                            continue

                        if diagonal_inflow:
                            #We want to measure the far side of the unit 
                            #triangle so we measure that angle UP from 
                            #theta = 0 on a unit circle
                            delta = np.pi/4-delta

                        #Taking absolute value because it might be on a 0,-45 
                        #degree angle
                        inflow_fraction = abs(np.tan(delta))
                        if not diagonal_inflow:
                            #If not diagonal then we measure the direct flow in
                            #which is the inverse of the tangent function
                            inflow_fraction = 1-inflow_fraction
                        
                        #Finally set the appropriate inflow variable

                        neighbor_flow = \
                            pixel_sediment_flow_array[neighbor_index]
                        if neighbor_flow == pixel_sediment_flow_nodata:
                            #Don't count undefined neighbor flow. DON'T DO IT!
                            continue
                        result[cell_index] += inflow_fraction * neighbor_flow

                except IndexError:
                    #This will occur if we visit a neighbor out of bounds
                    #it's okay, just skip it
                    pass

    pixel_retained_band.WriteArray(result.reshape((n_rows,n_cols)))
    return pixel_retained_dataset
