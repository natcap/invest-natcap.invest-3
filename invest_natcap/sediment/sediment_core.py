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

import invest_cython_core
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

    return potential_soil_loss_dataset


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

    #It's possible for the datasets to very slightly misalign, this is a
    #patch to make sure everything lines up for the moment
    datasets = [pixel_sediment_flow_dataset, retention_efficiency_dataset,
                flow_direction_dataset]

    aligned_dataset_uris = [tempfile.mkstemp(suffix='.tif')[1] for x in datasets]
    LOGGER.info(aligned_dataset_uris)
    aligned_datasets = raster_utils.align_datasets(
        datasets, aligned_dataset_uris)
    pixel_sediment_flow_dataset, retention_efficiency_dataset, flow_direction_dataset = \
        aligned_datasets

    pixel_sediment_flow_band, pixel_sediment_flow_nodata = \
        raster_utils.extract_band_and_nodata(pixel_sediment_flow_dataset)
    pixel_sediment_flow_array = pixel_sediment_flow_band.ReadAsArray().flatten()

    retention_efficiency_band, retention_efficiency_nodata = \
        raster_utils.extract_band_and_nodata(retention_efficiency_dataset)
    retention_efficiency_array = \
        retention_efficiency_band.ReadAsArray().flatten()

    flow_direction_band, flow_direction_nodata = \
        raster_utils.extract_band_and_nodata(flow_direction_dataset)
    flow_direction_array = flow_direction_band.ReadAsArray().flatten()

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

    result = numpy.zeros(n_rows*n_cols)

    #Determine the outflow directions based on index offsets.  It's written 
    #in terms of radian 4ths for easier readability and maintaince. 
    #Derived all this crap from page 36 in Rich's notes.
    inflow_directions = {( 0, 1): (4.0/4.0 * numpy.pi, 5, False),
                         (-1, 1): (5.0/4.0 * numpy.pi, 2, True),
                         (-1, 0): (6.0/4.0 * numpy.pi, 1, False),
                         (-1,-1): (7.0/4.0 * numpy.pi, 0, True),
                         ( 0,-1): (0.0/4.0 * numpy.pi, 3, False),
                         ( 1,-1): (1.0/4.0 * numpy.pi, 6, True),
                         ( 1, 0): (2.0/4.0 * numpy.pi, 7, False),
                         ( 1, 1): (3.0/4.0 * numpy.pi, 8, True)}

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
                    inflow_angle, _, diagonal_inflow = flow_properties
                    neighbor_index = calc_index(row_index+row_offset,
                                                col_index+col_offset)

                    #If this delta is within pi/4 it means there's an inflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(local_flow_angle - inflow_angle)

                    if delta < numpy.pi/4.0 or (2*numpy.pi - delta) < numpy.pi/4.0:
                        neighbor_retention = \
                            retention_efficiency_array[neighbor_index]
                        if neighbor_retention == retention_efficiency_nodata:
                            continue

                        if diagonal_inflow:
                            #We want to measure the far side of the unit 
                            #triangle so we measure that angle UP from 
                            #theta = 0 on a unit circle
                            delta = numpy.pi/4-delta

                        #Taking absolute value because it might be on a 0,-45 
                        #degree angle
                        inflow_fraction = abs(numpy.tan(delta))
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

    pixel_sediment_flow_dataset = None
    retention_efficiency_dataset = None
    flow_direction_dataset = None

    for uri in aligned_dataset_uris:
        try:
            os.remove(uri)
        except Exception:
            LOGGER.warn("Couldn't remove file %s" % uri)

    pixel_retained_band.WriteArray(result.reshape((n_rows, n_cols)))
    return pixel_retained_dataset

def burn_into_dataset(
    dataset, datasource, datasource_field, burn_value_dictionary, output_uri):
    """Burns a constant value into a dataset given a datasource and a 
        polygon in that datasource.

        dataset - gdal dataset to burn value into
        datasource - ogr dataset to use to mark the area to burn
        datasource_field - the name of the field in the datasource to 
           identify the feature we'll burn over
        burn_value_dictionary - 
            { datasource_value: value_to_burn_on_that_dataset, ...}

        returns nothing, but burns burn_value into dataset where 
           datasource.datasource_filed == datasource_value"""
    rasterize_options = ["ATTRIBUTE=%s" % datasource_field]
    layer = datasource.GetLayer()
    gdal.RasterizeLayer(dataset, [1], layer, burn_values=[1],
                        options = rasterize_options)

    raster_utils.reclassify_by_dictionary(
        dataset, burn_value_dictionary, output_uri, 'GTiff', -1.0,
        gdal.GDT_Float32)


def sum_over_region(dataset, aoi, mask_path = None, mask_field_value = None):
    """A function to aggregate the sum of all the pixels in dataset that
        overlap the aoi .

        dataset - a single band GDAL dataset
        aoi - an OGR datasource
        mask_path - (optional) a path to a file that can be written for 
            masking the dataset for aggregation.  If None then uses a
            memory raster the same size as dataset
        mask_field_value - (optional) a tuple links an attribute
            field name to field values that should be exclusively considered
            during a summation.  Example ('ws_id', 2)

        returns the sum of all the pixels in the first band of dataset
            that overlaps all the layers/features in aoi."""

    band, nodata = raster_utils.extract_band_and_nodata(dataset)

    if mask_path == None:
        mask_path = ''
        raster_type = 'MEM'
    else:
        raster_type = 'GTiff'

    mask_nodata = 255
    mask_dataset = raster_utils.new_raster_from_base(dataset, mask_path, 
        raster_type, mask_nodata, gdal.GDT_Byte)
    mask_band = mask_dataset.GetRasterBand(1)
    mask_band.Fill(mask_nodata)

    #Fill the mask with nodatas then add 1's everywhere there is a polygon
    for layer_id in xrange(aoi.GetLayerCount()):
        layer = aoi.GetLayer(layer_id)
        rasterize_options = ["ALL_TOUCHED=TRUE"]
        
        #if the mask field parameter is defined we'll burn the value of the
        #polygon field into the raster to filter out later
        if mask_field_value is not None:
            rasterize_options.append("ATTRIBUTE=%s" % mask_field_value[0])
        gdal.RasterizeLayer(mask_dataset, [1], layer, burn_values=[1],
                            options = rasterize_options)

    running_sum = 0.0

    #Loop through each row, set nodata values or mask field values to 0
    for row_index in range(band.YSize):
        row_array = band.ReadAsArray(0, row_index, band.XSize, 1)
        row_array[row_array == nodata] = 0

        mask_array = mask_band.ReadAsArray(0, row_index, band.XSize, 1)
        if mask_field_value is not None:
            #Mask out the field value based on the attribute value
            valid_mask = mask_array == mask_field_value[1]
        else:
            #if there is no field value than nodata is the only guide
            valid_mask = mask_array != mask_nodata

        #Set everything that's not valid to 0, then sum
        row_array[~valid_mask] = 0
        running_sum += numpy.sum(row_array)

    return running_sum

def generate_report(sediment_export_dataset, sediment_retained_dataset, 
                    watershed_aoi, output_table_uri):
    """Generates a CSV table that summarizes the amount of sediment retained
        in each watershed

        sediment_export_raster - a GDAL dataset whose values contain the amount
            of sediment exported on a given pixel
        sediment_retained_raster - a GDAL dataset whose values contain the amount
            of sediment retained on a given pixel
        watershed_aoi - an OGR datasource that contains a feature for each 
            watershed.  This will result in a row on each output table
        output_table_uri - a path to a csv file that will be created to dump
            the report to

        returns nothing, but writes a table to output_table_uri that contains
            -watershed id
            -sediment export
            -sediment export for dredging
            -sediment export for water quality"""
    
    watershed_layer = watershed_aoi.GetLayer()
    layer_definition = watershed_layer.GetLayerDefn()
    
    field_name_set = set()

    table_file = open(output_table_uri, 'w')

    for field_index in range(layer_definition.GetFieldCount()):
        field_definition = layer_definition.GetFieldDefn(field_index)
        field_name_set.add(field_definition.GetName())
        
    #Write the header row
    header_line = ''
    for field_name in field_name_set:
        header_line += field_name + ','
    #Add the output columns from the sediment model
    header_line += 'sed_exported,sed_retained\n'
    table_file.write(header_line)


    #create a new raster to hold the watershed level export values
    upret_sm_nodata = -1.0
    upret_sm_dataset = raster_utils.new_raster_from_base(
        sediment_export_dataset, '',
        'MEM', upret_sm_nodata, gdal.GDT_Float32)
    upret_sm_uri = os.path.join(os.path.dirname(output_table_uri), 'upret_sm.tif')
    upret_sm_band = upret_sm_dataset.GetRasterBand(1)
    upret_sm_band.Fill(upret_sm_nodata)


    #Now visit each feature to dump its feature values plus the calcualted
    #values from the sediment model
    id_to_export = {}
    for feature_index in range(watershed_layer.GetFeatureCount()):
        feature = watershed_layer.GetFeature(feature_index)
        value_line = ''
        #Dump the field values to the output row
        field_name = None
        for field_name in field_name_set:
            field_index = feature.GetFieldIndex(field_name)
            field_value = feature.GetField(field_index)
            value_line += str(field_value) + ','
            if field_name == 'id':
                watershed_id = field_value
        #Dump the calculated values to the output row
        #sediment export
        sed_export = \
            sum_over_region(sediment_export_dataset, watershed_aoi, 
            mask_path = None, mask_field_value = (field_name, field_value))
        sed_retained = \
            sum_over_region(sediment_retained_dataset, watershed_aoi, 
            mask_path = None, mask_field_value = (field_name, field_value))

        id_to_export[watershed_id] = sed_export

        value_line += str(sed_export) + ','
        #sediment retained
        value_line += str(sed_retained) + '\n'
        table_file.write(value_line)

    burn_into_dataset(upret_sm_dataset, watershed_aoi, 'id', id_to_export, upret_sm_uri)


def calculate_sdr(alpha_uri, flow_length_uri, slope_uri, sdr_uri):
    """Function to calculate the SDR component for retention percent

        alpha_uri - uri to gdal dataset that represents SDR alpha values
        flow_length_uri - uri to gdal dataset that represents cell flow lenghts
        slope_uri - uri to gdal dataset that represents slope percentages
        sdr_uri - uri to write the sdr out to

        returns nothing"""

    alpha_dataset = gdal.Open(alpha_uri)
    _, alpha_nodata = raster_utils.extract_band_and_nodata(alpha_dataset)

    flow_length_dataset = gdal.Open(flow_length_uri)
    _, flow_length_nodata = raster_utils.extract_band_and_nodata(flow_length_dataset)

    LOGGER.debug(slope_uri)
    slope_dataset = gdal.Open(slope_uri)
    _, slope_nodata = raster_utils.extract_band_and_nodata(slope_dataset)

    sdr_nodata = -1.0


    def sdr_calc(flow_length, alpha, slope):
        """This is the SDR calculation from Yonas's writeup on dropbox called
            InVEST Sediment Model_modifications_10-01-2012_RS.dcx"""
        if flow_length == flow_length_nodata or alpha == alpha_nodata or \
                slope == slope_nodata:
            return sdr_nodata
        if slope == 0.0:
            return 0.0
        t_ij = flow_length/(alpha*numpy.sqrt(slope))
        return numpy.exp(-t_ij)

    dataset_list = [flow_length_dataset, alpha_dataset, slope_dataset]
    raster_utils.vectorize_rasters(
        dataset_list, sdr_calc, raster_out_uri=sdr_uri,
        datatype=gdal.GDT_Float32, nodata=sdr_nodata)
