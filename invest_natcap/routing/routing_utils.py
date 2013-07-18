"""This file contains functions to simulate overland flow on GIS rasters
    defined by DEM raster datasets.  Here are some conventions of this model:

    A single pixel defines its neighbors as follows:

    3 2 1
    4 p 0
    5 6 7

    The 'p' refers to 'pixel' since the flow model is pixel centric.

    One of the outputs from this model will be a flow graph represented as a
    sparse matrix.  The rows in the matrix are the originating nodes and the
    columns represent the outflow, thus G[i,j]'s value is the fraction of flow
    from node 'i' to node 'j'.  The following expresses how to calculate the
    matrix indexes from the pixels original row,column position in the raster.
    Given that the raster's dimension is 'n_rows' by 'n_columns', pixel located
    at row 'r' and colunn 'c' has index

        (r,c) -> r * n_columns + c = index

    Likewise given 'index' r and c can be derived as:

        (index) -> (index div n_columns, index mod n_columns) where 'div' is
            the integer division operator and 'mod' is the integer remainder
            operation."""

import logging
import tempfile
import os

from osgeo import gdal
import numpy

from invest_natcap import raster_utils
import routing_cython_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing')


def route_flux(in_dem_uri, in_source_uri, in_absorption_rate_uri, loss_uri,
               flux_uri, absorption_mode, aoi_uri=None):

    """This function will route flux across a landscape given a dem to
        guide flow from a d-infinty flow algorithm, and a custom function
        that will operate on input flux and other user defined arguments
        to determine nodal output flux.

        dem_uri - a URI to a DEM raster
        source_uri - a GDAL dataset that has source flux per pixel
        absorption_rate_uri - a GDAL floating point dataset that has a percent
            of flux absorbed per pixel
        loss_uri - an output URI to to the dataset that will output the
            amount of flux absorbed by each pixel
        flux_uri - a URI to an output dataset that records the amount of flux
            traveling through each pixel
        absorption_mode - either 'flux_only' or 'source_and_flux'. For
            'flux_only' the outgoing flux is (in_flux * absorption + source).
            If 'source_and_flux' then the output flux
            is (in_flux + source) * absorption.
        aoi_uri - an OGR datasource for an area of interest polygon.
            the routing flux calculation will only occur on those pixels
            and neighboring pixels will either be raw outlets or
            non-contibuting inputs depending on the orientation of the DEM.

        returns nothing"""

    #this is for debugging the routing issues
    out_dir = os.path.dirname(in_dem_uri)

    dem_uri = os.path.join(out_dir, 'aligned_dem_uri.tif')
    #dem_uri = raster_utils.temporary_filename()
#    source_uri = raster_utils.temporary_filename()
#    absorption_rate_uri = raster_utils.temporary_filename()
    source_uri = os.path.join(out_dir, 'aligned_source_uri.tif')
    absorption_rate_uri = os.path.join(out_dir, 'aligned_absorption_uri.tif')
    out_pixel_size = raster_utils.get_cell_size_from_uri(in_dem_uri)
    raster_utils.align_dataset_list(
        [in_dem_uri, in_source_uri, in_absorption_rate_uri],
        [dem_uri, source_uri, absorption_rate_uri],
        ["nearest", "nearest", "nearest"], out_pixel_size,
        "intersection", 0, aoi_uri=aoi_uri)

    flow_direction_uri = os.path.join(out_dir, 'aligned_flow_uri.tif')
    outflow_weights_uri = os.path.join(out_dir, 'aligned_outflow_weight_uri.tif')
    outflow_direction_uri = os.path.join(out_dir, 'aligned_outflow_direction_uri.tif')
#    flow_direction_uri = raster_utils.temporary_filename()
#    outflow_weights_uri = raster_utils.temporary_filename()
#    outflow_direction_uri = raster_utils.temporary_filename()

    routing_cython_core.calculate_flow_direction(dem_uri, flow_direction_uri)
    sink_cell_set, _ = routing_cython_core.calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri,
        dem_uri)
    routing_cython_core.calculate_transport(
        outflow_direction_uri, outflow_weights_uri, sink_cell_set,
        source_uri, absorption_rate_uri, loss_uri, flux_uri, absorption_mode)


def flow_accumulation(dem_uri, flux_output_uri):
    """A helper function to calculate flow accumulation, also returns
        intermediate rasters for future calculation.

        dem_uri - a uri to a gdal dataset representing a DEM
        flux_output_uri - location to dump the raster represetning flow
            accumulation"""

    constant_flux_source_uri = raster_utils.temporary_filename()
    zero_absorption_source_uri = raster_utils.temporary_filename()
    loss_uri = raster_utils.temporary_filename()

    make_constant_raster_from_base(
        dem_uri, 1.0, constant_flux_source_uri)
    make_constant_raster_from_base(
        dem_uri, 0.0, zero_absorption_source_uri)

    route_flux(
        dem_uri, constant_flux_source_uri,
        zero_absorption_source_uri, loss_uri, flux_output_uri, 'flux_only')


def make_constant_raster_from_base(base_dataset_uri, constant_value, out_uri):
    """A helper function that creates a new gdal raster from base, and fills
        it with the constant value provided.

        base_dataset_uri - the gdal base raster
        constant_value - the value to set the new base raster to
        out_uri - the uri of the output raster

        returns nothing"""

    base_dataset = gdal.Open(base_dataset_uri)
    out_dataset = raster_utils.new_raster_from_base(
        base_dataset, out_uri, 'GTiff', constant_value - 1,
        gdal.GDT_Float32)
    out_band, _ = raster_utils.extract_band_and_nodata(out_dataset)
    out_band.Fill(constant_value)


def stream_threshold(flow_accumulation_uri, flow_threshold, stream_uri):
    """Creates a raster of accumulated flow to each cell.

        flow_accumulation_data - (input) A flow accumulation dataset of type
            floating point
        flow_threshold - (input) a number indicating the threshold to declare
            a pixel a stream or no
        stream_uri - (input) the uri of the output stream dataset

        returns nothing"""

    flow_accumulation_dataset = gdal.Open(flow_accumulation_uri)
    stream_nodata = 255
    stream_dataset = raster_utils.new_raster_from_base(
        flow_accumulation_dataset, stream_uri, 'GTiff', stream_nodata,
        gdal.GDT_Byte)
    stream_band = stream_dataset.GetRasterBand(1)
    stream_band.Fill(stream_nodata)
    stream_data_file = tempfile.TemporaryFile()
    stream_array = raster_utils.load_memory_mapped_array(
        stream_uri, stream_data_file)
    stream_array[:] = stream_nodata

    flow_accumulation_data_file = tempfile.TemporaryFile()
    flow_accumulation_array = raster_utils.load_memory_mapped_array(
        flow_accumulation_uri, flow_accumulation_data_file)

    _, flow_accumulation_nodata = \
        raster_utils.extract_band_and_nodata(flow_accumulation_dataset)

    stream_array[(flow_accumulation_array != flow_accumulation_nodata) *
                 (flow_accumulation_array >= float(flow_threshold))] = 1
    stream_array[(flow_accumulation_array != flow_accumulation_nodata) *
                 (flow_accumulation_array < float(flow_threshold))] = 0

    stream_band.WriteArray(stream_array)


def calculate_flow_length(flow_direction_uri, flow_length_uri):
    """Calcualte the flow length of a cell given the flow direction

        flow_direction_uri - uri to a gdal dataset that represents the
            d_inf flow direction of each pixel
        flow_length_uri - the uri that the output flow length will be put to

        returns nothing"""

    flow_direction_dataset = gdal.Open(flow_direction_uri)
    _, flow_direction_nodata = raster_utils.extract_band_and_nodata(
        flow_direction_dataset)

    flow_length_nodata = -1.0
    flow_length_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, flow_length_uri, 'GTiff', flow_length_nodata,
        gdal.GDT_Float32)

    flow_length_pixel_size = raster_utils.pixel_size(flow_length_dataset)

    def flow_length(flow_direction):
        """Function to calculate flow length for vectorize_rasters"""
        if flow_direction == flow_direction_nodata:
            return flow_length_nodata
        sin_val = numpy.abs(numpy.sin(flow_direction))
        cos_val = numpy.abs(numpy.cos(flow_direction))
        return flow_length_pixel_size / numpy.maximum(sin_val, cos_val)

    raster_utils.vectorize_rasters(
        [flow_direction_dataset], flow_length, aoi=None,
        raster_out_uri=flow_length_uri, datatype=gdal.GDT_Float32,
        nodata=flow_length_nodata)


def pixel_amount_exported(in_dem_uri, in_stream_uri, in_retention_rate_uri, 
                          in_source_uri, pixel_export_uri, aoi_uri=None):
    """Calculates flow and absorption rates to determine the amount of source
        exported to the stream.  All datasets must be in the same projection.
        Nothing will be retained on stream pixels.

        in_dem_uri - a dem dataset used to determine flow directions
        in_stream_uri - an integer dataset representing stream locations.
            0 is no stream 1 is a stream
        in_retention_rate_uri - a dataset representing per pixel retention
            rates
        in_source_uri - a dataset representing per pixel export
        pixel_export_uri - the output dataset uri to represent the amount
            of source exported to the stream

        returns nothing"""

    #Align all the input rasters since the cython core requires them to line up
    out_pixel_size = raster_utils.get_cell_size_from_uri(in_dem_uri)
    dem_uri = raster_utils.temporary_filename()
    stream_uri = raster_utils.temporary_filename()
    retention_rate_uri = raster_utils.temporary_filename()
    source_uri = raster_utils.temporary_filename()
    raster_utils.align_dataset_list(
        [in_dem_uri, in_stream_uri, in_retention_rate_uri, in_source_uri],
        [dem_uri, stream_uri, retention_rate_uri, source_uri],
        ["nearest", "nearest", "nearest", "nearest"], out_pixel_size,
        "intersection", 0, aoi_uri=aoi_uri)

    #Calculate export rate
    export_rate_uri = raster_utils.temporary_filename()
    nodata_retention = raster_utils.get_nodata_from_uri(retention_rate_uri)
    def retention_to_export(retention):
        """calculates 1.0-input unles it's nodata"""
        if retention == nodata_retention:
            return nodata_retention
        return 1.0 - retention
    raster_utils.vectorize_datasets(
        [retention_rate_uri], retention_to_export, export_rate_uri,
        gdal.GDT_Float32, nodata_retention, out_pixel_size, "intersection",
        dataset_to_align_index=0)

    #Calculate flow direction and weights
    flow_direction_uri = raster_utils.temporary_filename()
    routing_cython_core.calculate_flow_direction(dem_uri, flow_direction_uri)
    outflow_weights_uri = raster_utils.temporary_filename()
    outflow_direction_uri = raster_utils.temporary_filename()
    routing_cython_core.calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)

    #Calculate the percent to sink
    effect_uri = raster_utils.temporary_filename()
    routing_cython_core.percent_to_sink(
        stream_uri, export_rate_uri, outflow_direction_uri,
        outflow_weights_uri, effect_uri)

    #Finally multiply the effect by the source
    nodata_source = raster_utils.get_nodata_from_uri(source_uri)
    nodata_effect = raster_utils.get_nodata_from_uri(effect_uri)
    nodata_stream = raster_utils.get_nodata_from_uri(stream_uri)
    def mult_nodata(source, effect, stream):
        """Does the multiply of source by effect if there's not a stream"""
        if source == nodata_source or effect == nodata_effect or \
                stream == nodata_stream:
            return nodata_source
        return source * effect * (1 - stream)
    raster_utils.vectorize_datasets(
        [source_uri, effect_uri, stream_uri], mult_nodata, pixel_export_uri,
        gdal.GDT_Float32, nodata_source, out_pixel_size, "intersection",
        dataset_to_align_index=0)


def calculate_stream(dem_uri, flow_threshold, stream_uri):
    """A wrapper to calculate streams given a dem and a flow threshold.
        The function will calcluate the flow accumulation then threshold
        that to calcualte streams.  Useful to sidestep separate flow
        accumulation.

        dem_uri - a uri to a gdal dataset describing the dem
        flow_threshold - the value to determine if a flow pixel is a stream
            pixel
        stream_uri - a uri to an output dataset that will have pixels
            listed a 0 for no stream or 1 for stream or nodata outside the dem

        returns nothing"""

    flow_accumulation_uri = raster_utils.temporary_filename()
    flow_accumulation(dem_uri, flow_accumulation_uri)
    stream_threshold(flow_accumulation_uri, flow_threshold, stream_uri)


def flow_direction_inf(dem_uri, flow_direction_uri):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.
        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

       dem_uri - (input) a uri to a single band GDAL Dataset with elevation
           values
       flow_direction_uri - (output) a uri to a single band GDAL dataset
           with d infinity flow directions in it.

       returns nothing"""
    routing_cython_core.flow_direction_inf(dem_uri, flow_direction_uri)
