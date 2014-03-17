"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import logging
import bisect

import numpy
from osgeo import gdal

from invest_natcap import raster_utils
import sediment_cython_core

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
            the slope at a pixel given as a percent
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
            slope - slope in terms of percent
            flow_accumulation - upstream pixels at this point

            returns the ls_factor calculation for this point"""

        #Skip the calculation if any of the inputs are nodata
        nodata_mask = (
            (aspect_angle == aspect_nodata) | (slope == slope_nodata) |
            (flow_accumulation == flow_accumulation_nodata))
        
        #Here the aspect direction can range from 0 to 2PI, but the purpose
        #of the term is to determine the length of the flow path on the
        #pixel, thus we take the absolute value of each trigonometric
        #function to keep the computation in the first quadrant
        xij = (numpy.abs(numpy.sin(aspect_angle)) +
            numpy.abs(numpy.cos(aspect_angle)))

        contributing_area = (flow_accumulation-1) * cell_area

        #To convert to radians, we need to divide the slope by 100 since
        #it's a percent. :(
        slope_in_radians = numpy.arctan(slope / 100.0)

        #From Equation 4 in "Extension and validation of a geographic
        #information system ..."
        slope_factor = numpy.where(slope < 9.0,
            10.8 * numpy.sin(slope_in_radians) + 0.03, 
            16.8 * numpy.sin(slope_in_radians) - 0.5)
        
        #Set the m value to the lookup table that's Table 1 in 
        #InVEST Sediment Model_modifications_10-01-2012_RS.docx in the
        #FT Team dropbox
        beta = ((numpy.sin(slope_in_radians) / 0.0896) /
            (3 * numpy.sin(slope_in_radians)**0.8 + 0.56))

        #slope table in percent
        slope_table = [1., 3.5, 5., 9.]
        exponent_table = [0.2, 0.3, 0.4, 0.5]
        #Look up the correct m value from the table
        m_exp = beta/(1+beta)
        for i in range(4):
            m_exp[slope <= slope_table[i]] = exponent_table[i]
                
        #The length part of the ls_factor:
        l_factor = (
            ((contributing_area + cell_area)**(m_exp+1) - 
             contributing_area ** (m_exp+1)) / 
            ((cell_size ** (m_exp + 2)) * (xij**m_exp) * (22.13**m_exp)))

        #From the McCool paper "as a final check against excessively long slope
        #length calculations ... cap of 333m"
        l_factor[l_factor > 333] = 333
            
        #This is the ls_factor
        return numpy.where(nodata_mask, ls_nodata, l_factor * slope_factor)
        
    #Call vectorize datasets to calculate the ls_factor
    dataset_uri_list = [aspect_uri, slope_uri, flow_accumulation_uri]
    raster_utils.vectorize_datasets(
        dataset_uri_list, ls_factor_function, ls_factor_uri, gdal.GDT_Float32,
        ls_nodata, cell_size, "intersection", dataset_to_align_index=0,
        vectorize_op=False)


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
    cell_area_ha = cell_size ** 2 / 10000.0

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

        rkls = numpy.where(
            v_stream == 1, 0.0,
            ls_factor * erosivity * erodibility * cell_area_ha)
        return numpy.where(
            (ls_factor == ls_factor_nodata) | (erosivity == erosivity_nodata) |
            (erodibility == erodibility_nodata) | (v_stream == stream_nodata),
            usle_nodata, rkls)
        
    dataset_uri_list = [
        ls_factor_uri, erosivity_uri, erodibility_uri, stream_uri]

    #Aligning with index 3 that's the stream and the most likely to be
    #aligned with LULCs
    raster_utils.vectorize_datasets(
        dataset_uri_list, rkls_function, rkls_uri, gdal.GDT_Float32,
        usle_nodata, cell_size, "intersection", dataset_to_align_index=3,
        vectorize_op=False)
