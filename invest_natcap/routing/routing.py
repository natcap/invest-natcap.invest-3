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


def calculate_routing(
    dem_uri, dataset_uri_list, op, workspace_dir, raster_out_uri,
    out_nodata_value, aoi_uri = None):

    """This function will route flux across a landscape given a dem to
        guide flow from a d-infinty flow algorithm, and a custom function
        that will operate on input flux and other user defined arguments
        to determine nodal output flux.

        dem_uri - a URI to a DEM raster
        dataset_uri_list - a list of GDAL readable rasters that will be
            used as input to the 'op' operation.  These datasets
            must be aligned with themselves and dem_uri.
        op - a len(dataset_uri_list)+1 function that operates per pixel
            on the aligned pixel stack from dataset_uri_list where the
            first input is the incoming flux from other contributing 
            nodes.
        workspace_dir - a directory that can be used for intermediate
            file generation.  The contents of this directory are not safe
            for preseveration if files already exist in it.
        raster_out_uri - the name/uri of the output raster?  TODO: WHAT OUTPUTS?
        out_nodata_value - the nodata value of the ouput raster TODO: RASTERS?
        aoi_uri - an OGR datasource for an area of interest polygon.
            the routing flux calculation will only occur on those pixels
            and neighboring pixels will either be raw outlets or 
            non-contibuting inputs depending on the orientation of the DEM.

        returns nothing"""

    pass
