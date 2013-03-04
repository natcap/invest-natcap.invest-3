"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import bisect
import os
import tempfile

import scipy.sparse
import scipy.sparse.linalg
import numpy
from osgeo import gdal
from osgeo import ogr

from invest_natcap.routing import routing_utils
from invest_natcap import raster_utils

LOGGER = logging.getLogger('sediment_core')


def calculate_ls_factor(flow_accumulation_uri, slope_uri, 
                        aspect_uri, ls_factor_uri, ls_nodata):
    """Calculates the LS factor as Equation 3 from "Extension and validation 
        of a geographic information system-based method for calculating the
        Revised Universal Soil Loss Equation length-slope factor for erosion
        risk assessments in large watersheds"   

        (Required that all raster inputs are same dimensions and projections
        and have square cells)
        flow_accumulation_uri - a uri to a  single band raster of type float that
            indicates the contributing area at the inlet of a grid cell
        slope_uri - a uri to a single band raster of type float that indicates
            the slope at a pixel given as a proportion (e.g. a value of 0.05
            is a slope of 5%)
        aspect_uri - a uri to a single band raster of type float that indicates the
            direction that slopes are facing in terms of radians east and
            increase clockwise: pi/2 is north, pi is west, 3pi/2, south and
            0 or 2pi is east.
        ls_factor_uri - (input) a string to the path where the LS raster will
            be written

        returns nothing"""
    
    flow_accumulation_nodata = raster_utils.get_nodata_from_uri(
        flow_accumulation_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)
    aspect_nodata = raster_utils.get_nodata_from_uri(aspect_uri)

    #Assumes that cells are square
    cell_size = raster_utils.get_cell_size_from_uri(flow_accumulation_uri)
    cell_area = cell_size ** 2

    def ls_factor_function(aspect_angle, slope, flow_accumulation):
        """Calculate the ls factor

            aspect_angle - flow direction in radians
            slope - slope in terms of (units?)
            flow_accumulation - upstream pixels at this point

            returns the ls_factor calculation for this point"""

        #Skip the calculation if any of the inputs are nodata
        if aspect_angle == aspect_nodata or slope == slope_nodata or \
                flow_accumulation == flow_accumulation_nodata:
            return ls_nodata

        #Here the aspect direciton can range from 0 to 2PI, but the purpose
        #of the term is to determine the length of the flow path on the
        #pixel, thus we take the absolute value of each trigometric
        #function to keep the computation in the first quadrant
        xij = abs(numpy.sin(aspect_angle)) + abs(numpy.cos(aspect_angle))

        contributing_area = (flow_accumulation-1) * cell_area

        #To convert to radians, we need to divide the slope by 100 since
        #it's a percent. :(
        slope_in_radians = numpy.arctan(slope / 100.0)

        #From Equation 4 in "Extension and validataion of a geographic
        #information system ..."
        if slope < 9:
            slope_factor =  10.8 * numpy.sin(slope_in_radians) + 0.03
        else:
            slope_factor =  16.8 * numpy.sin(slope_in_radians) - 0.5
            
        #Set the m value to the lookup table that's Table 1 in 
        #InVEST Sediment Model_modifications_10-01-2012_RS.docx in the
        #FT Team dropbox
        beta = (numpy.sin(slope_in_radians) / 0.0896) / \
            (3 * pow(numpy.sin(slope_in_radians),0.8) + 0.56)
        slope_table = [0.01, 0.035, 0.05, 0.09]
        exponent_table = [0.2, 0.3, 0.4, 0.5, beta/(1+beta)]
            
        #Use the bisect function to do a nifty range 
        #lookup. http://docs.python.org/library/bisect.html#other-examples
        m = exponent_table[bisect.bisect(slope_table, slope)]

        #The length part of the ls_factor:
        ls_factor = ((contributing_area + cell_area)**(m+1) - \
                         contributing_area ** (m+1)) / \
                         ((cell_size ** (m + 2)) * (xij**m) * (22.13**m))

        #From the paper "as a final check against exessively long slope
        #length calculations ... cap of 333m"
        if ls_factor > 333:
            ls_factor = 333
                
        return ls_factor * slope_factor

    #Call vectorize datasets to calculate the ls_factor
    dataset_uri_list = [aspect_uri, slope_uri, flow_accumulation_uri]
    raster_utils.vectorize_datasets(
        dataset_uri_list, ls_factor_function, ls_factor_uri, gdal.GDT_Float32,
            ls_nodata, cell_size, "intersection", dataset_to_align_index=0)


def calculate_potential_soil_loss(
    ls_factor_uri, erosivity_uri, erodibility_uri, cp_uri, stream_uri,
    usle_uri):

    """Calculates per-pixel potential soil loss using the RUSLE (revised 
        universial soil loss equation).

        ls_factor_uri - GDAL uri with the LS factor pre-calculated
        erosivity_uri - GDAL uri with per pixel erosivity 
        erodibility_uri - GDAL uri with per pixel erodibility
        c_uri - GDAL uri per pixel crop managment factor
        p_uri - GDAL uri per pixel land management factor
        stream_uri - GDAL uri indicating locations with streams
            (0 is no stream, 1 stream)
        usle_uri - string input indicating the path to disk
            for the resulting potential soil loss raster

        returns nothing"""

    ls_factor_nodata = raster_utils.get_nodata_from_uri(ls_factor_uri)
    erosivity_nodata = raster_utils.get_nodata_from_uri(erosivity_uri)
    erodibility_nodata = raster_utils.get_nodata_from_uri(erodibility_uri)
    cp_nodata = raster_utils.get_nodata_from_uri(cp_uri)
    stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)

    usle_nodata = -1.0
    ls_factor_nodata = -1.0

    cell_size = raster_utils.get_cell_size_from_uri(cp_uri)
    cell_area = cell_size ** 2

    def usle_function(ls_factor, erosivity, erodibility, usle_cp,
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
            erodibility == erodibility_nodata or usle_cp == cp_nodata or \
            v_stream == stream_nodata:
            return usle_nodata
        if v_stream == 1:
            return 0.0
        #current unit is tons/ha, multiply by ha/cell (cell area in m^2/100**2)
        return (
            ls_factor * erosivity * erodibility * usle_cp * cell_area / 10000.0)

    dataset_uri_list = [
        ls_factor_uri, erosivity_uri, erodibility_uri, cp_uri, stream_uri]

    #Aligning with index 4 because that's cp and the most likely to be
    #aligned with LULCs
    raster_utils.vectorize_datasets(
        dataset_uri_list, usle_function, usle_uri, gdal.GDT_Float32,
        usle_nodata, cell_size, "intersection", dataset_to_align_index=4)


def calculate_rkls(
    ls_factor_uri, erosivity_uri, erodibility_uri, stream_uri,
    rkls_uri):

    """Calculates per-pixel potential soil loss using the RKLS (revised 
        universial soil loss equation with no C or P).

        ls_factor_uri - GDAL uri with the LS factor pre-calculated
        erosivity_uri - GDAL uri with per pixel erosivity 
        erodibility_uri - GDAL uri with per pixel erodibility
        stream_uri - GDAL uri indicating locations with streams
            (0 is no stream, 1 stream)
        rkls_uri - string input indicating the path to disk
            for the resulting potential soil loss raster

        returns nothing"""

    ls_factor_nodata = raster_utils.get_nodata_from_uri(ls_factor_uri)
    erosivity_nodata = raster_utils.get_nodata_from_uri(erosivity_uri)
    erodibility_nodata = raster_utils.get_nodata_from_uri(erodibility_uri)
    stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)
    usle_nodata = -1.0

    cell_size = raster_utils.get_cell_size_from_uri(ls_factor_uri)
    cell_area = cell_size ** 2

    def rkls_function(ls_factor, erosivity, erodibility, v_stream):
        """Calculates the USLE equation
        
        ls_factor - length/slope factor
        erosivity - related to peak rainfall events
        erodibility - related to the potential for soil to erode
        v_stream - 1 or 0 depending if there is a stream there.  If so, no
            potential soil loss due to USLE
        
        returns ls_factor * erosivity * erodibility * usle_c_p if all arguments
            defined, nodata if some are not defined, 0 if in a stream
            (v_stream)"""

        if (ls_factor == ls_factor_nodata or erosivity == erosivity_nodata or 
            erodibility == erodibility_nodata or v_stream == stream_nodata):
            return usle_nodata
        if v_stream == 1:
            return 0.0
        #current unit is tons/ha, multiply by ha/cell (cell area in m^2/100**2)
        return ls_factor * erosivity * erodibility * cell_area / 10000.0

    dataset_uri_list = [
        ls_factor_uri, erosivity_uri, erodibility_uri, stream_uri]

    #Aligning with index 3 that's the stream and the most likely to be
    #aligned with LULCs
    raster_utils.vectorize_datasets(
        dataset_uri_list, rkls_function, rkls_uri, gdal.GDT_Float32,
        usle_nodata, cell_size, "intersection", dataset_to_align_index=3)
