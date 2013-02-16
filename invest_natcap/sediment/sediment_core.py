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
    
    #Tease out all the nodata values for reading and setting
    flow_accumulation_dataset = gdal.Open(flow_accumulation_uri)
    slope_dataset = gdal.Open(slope_uri)
    aspect_dataset = gdal.Open(aspect_uri)

    _, flow_accumulation_nodata = \
        raster_utils.extract_band_and_nodata(flow_accumulation_dataset)
    _, slope_nodata = raster_utils.extract_band_and_nodata(slope_dataset)
    _, aspect_nodata = raster_utils.extract_band_and_nodata(aspect_dataset)

    #Assumes that cells are square
    cell_size = abs(flow_accumulation_dataset.GetGeoTransform()[1])
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

    #Call vectorize rasters for ls_factor
    dataset_list = [aspect_dataset, slope_dataset, flow_accumulation_dataset]

    ls_factor_dataset = \
        raster_utils.vectorize_rasters(dataset_list, ls_factor_function, \
            raster_out_uri=ls_factor_uri, datatype=gdal.GDT_Float32, \
            nodata=ls_nodata)

    raster_utils.calculate_raster_stats(ls_factor_dataset)


def calculate_potential_soil_loss(ls_factor_uri, erosivity_uri, 
                                  erodibility_uri, cp_uri,
                                  stream_uri, usle_uri):

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

    ls_factor_dataset = gdal.Open(ls_factor_uri)
    erosivity_dataset = gdal.Open(erosivity_uri)
    erodibility_dataset = gdal.Open(erodibility_uri)
    cp_dataset = gdal.Open(cp_uri)
    stream_dataset = gdal.Open(stream_uri)


    _, ls_factor_nodata = \
        raster_utils.extract_band_and_nodata(ls_factor_dataset)
    _, erosivity_nodata = \
        raster_utils.extract_band_and_nodata(erosivity_dataset)
    _, erodibility_nodata = \
        raster_utils.extract_band_and_nodata(erodibility_dataset)
    _, cp_nodata = \
        raster_utils.extract_band_and_nodata(cp_dataset)
    _, stream_nodata = \
        raster_utils.extract_band_and_nodata(stream_dataset)

    usle_nodata = -1.0
    ls_factor_nodata = -1.0
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
        return ls_factor * erosivity * erodibility * usle_cp

    dataset_list = [ls_factor_dataset, erosivity_dataset, erodibility_dataset, 
                    cp_dataset, stream_dataset]

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


def aggregate_raster_values(
    dataset_uri, shapefile_uri, operation, shapefile_id_field, ignore_nodata=True):
    """Collect all the dataset values that lie in shapefile depending on the value
        of operation

        dataset - a GDAL dataset of some sort of value
        shapefile_uri - an OGR datasource that probably overlaps dataset
        operation - a string of one of ['mean', 'sum']
        ignore_nodata - (optional) if operation == 'mean' then it does not account
            for nodata pixels when determing the average, otherwise all pixels in
            the AOI are used for calculation of the mean.
        shapefile_id_field - the field to uniquely identify polygons
        returns a dictionary whose keys are the values in shapefile_field and values
            are the aggregated values over dataset.  If no values are aggregated
            contains 0."""
    
    #Generate a temporary mask filename
    temporary_mask_filename = raster_utils.temporary_filename()
    dataset = gdal.Open(dataset_uri)
    dataset_band = dataset.GetRasterBand(1)
    dataset_nodata = float(dataset_band.GetNoDataValue())
    pixel_size_out = raster_utils.pixel_size(dataset)

    clipped_dataset_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [dataset_uri], lambda x: float(x), clipped_dataset_uri,
        gdal.GDT_Float32, dataset_nodata, pixel_size_out, "intersection",
        dataset_to_align_index=0, aoi_uri=shapefile_uri)
    clipped_dataset = gdal.Open(clipped_dataset_uri)
    clipped_band = clipped_dataset.GetRasterBand(1)

    #This should be a value that's not in shapefile[shapefile_field]
    mask_nodata = -1.0
    mask_dataset = raster_utils.new_raster_from_base(clipped_dataset, 
        temporary_mask_filename, 'GTiff', mask_nodata, gdal.GDT_Int32)
    mask_band = mask_dataset.GetRasterBand(1)
    mask_band.Fill(mask_nodata)

    shapefile = ogr.Open(shapefile_uri)
    shapefile_layer = shapefile.GetLayer()
    gdal.RasterizeLayer(mask_dataset, [1], shapefile_layer,
                        options = ['ATTRIBUTE=%s' % shapefile_id_field])

    mask_dataset.FlushCache()
    mask_band = mask_dataset.GetRasterBand(1)

    #This will store the sum/count with index of shapefile attribute
    aggregate_dict_values = {}
    aggregate_dict_counts = {}

    #Loop over each row in out_band
    for row_index in range(clipped_band.YSize):
        mask_array = mask_band.ReadAsArray(0,row_index,mask_band.XSize,1)
        clipped_array = clipped_band.ReadAsArray(0,row_index,clipped_band.XSize,1)


        for attribute_id in numpy.unique(mask_array):
            #ignore masked values
            if attribute_id == mask_nodata:
                continue

            #Only consider values which lie in the polygon for attribute_id
            masked_values = clipped_array[mask_array == attribute_id]
            if ignore_nodata:
                #Only consider values which are not nodata values
                masked_values = masked_values[masked_values != dataset_nodata]
                attribute_sum = numpy.sum(masked_values)
            else:
                #We leave masked_values alone, but only sum the non-nodata 
                #values
                attribute_sum = \
                    numpy.sum(masked_values[masked_values != dataset_nodata])

            try:
                aggregate_dict_values[attribute_id] += attribute_sum
                aggregate_dict_counts[attribute_id] += masked_values.size
            except KeyError:
                aggregate_dict_values[attribute_id] = attribute_sum
                aggregate_dict_counts[attribute_id] = masked_values.size
            
    result_dict = {}
    for attribute_id in aggregate_dict_values:
        if operation == 'sum':
            result_dict[attribute_id] = aggregate_dict_values[attribute_id]
        elif operation == 'mean':
            if aggregate_dict_counts[attribute_id] != 0.0:
                result_dict[attribute_id] = aggregate_dict_values[attribute_id] / \
                    aggregate_dict_counts[attribute_id]
            else:
                result_dict[attribute_id] = 0.0
        else:
            LOGGER.warn("%s operation not defined" % operation)
    
    return result_dict
