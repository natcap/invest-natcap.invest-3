import os

from osgeo import gdal, ogr

from invest_natcap import raster_utils

from scipy.linalg import eig
import scipy.ndimage

import disk_sort

from decimal import Decimal
from fractions import Fraction

import numpy

import logging

import struct

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('scenario_generator')


def calculate_weights(arr, rounding=4):
   places = Decimal(10) ** -(rounding)

   # get eigenvalues and vectors
   eigenvalues, eigenvectors = eig(arr)

   # get primary eigenvalue and vector
   primary_eigenvalue = max(eigenvalues)
   primary_eigenvalue_index = eigenvalues.tolist().index(primary_eigenvalue)
   primary_eigenvector = eigenvalues.take((primary_eigenvalue_index,), axis=1)

   # priority vector = normalized primary eigenvector

   normalized = eigenvector / sum(eigenvector)

   # turn into list of real part values
   vector = [abs(e[0]) for e in normalized]

   # return nice rounded Decimal values with labels
   return [ Decimal( str(v) ).quantize(places) for v in vector ]

def calulcate_priority(table_uri, attributes_uri=None):
    table_file = open(table_uri,'r')
    table = [line.split(",") for line in table_file]
    table_file.close()

    #format table
    for row_id, line in enumerate(table):
        for column_id in range(row_id+1):
            table[row_id][column_id]=Fraction(table[row_id][column_id])
            if row_id != column_id:
                table[column_id][row_id]=1/Fraction(table[row_id][column_id])

    matrix = numpy.array(table)

    return calculate_weights(matrix, 4)

def prepare_landattrib_array(landcover_uri, transition_uri, transition_key_field):
    """
    Table expected to contain the following columns in order:

    0 LULC    The land cover code
    1 SHORTNME  The land cover short name (max 12 characters)
    2 COUNT  Number of pixels in each LULC class
    3 PIXELCHANGE  The number of pixels expected to change
    4 PRIORITY  The priority of this landcover (objective)
    5 PROXIMITY Is this landcover suitability affected by proximity, eg do pixels
                closer to agriculture have higher chances of converting to agriculture [0,1]
    6 PROXDIST  At what distance does the proximity influence die? (in meters, default 10,000m)
    7 PATCHHA Minimum size of patch
    8 F1...Fn  The matching landcover probability score for the matrix. n corresponds to LULC
    """

    raster_utils.get_lookup_from_csv(trasition_uri, transition_key_field)
    ratser_utils.unique_raster_values_count(landcover_uri)

   #convert change amount to pixels?

def calculate_distance_raster_uri(dataset_in_uri, dataset_out_uri, cell_size = None):
    if cell_size == None:
       cell_size = raster_utils.get_cell_size_from_uri(dataset_in_uri)

    memory_array = raster_utils.load_memory_mapped_array(dataset_in_uri, raster_utils.temporary_filename())

    memory_array = scipy.ndimage.morphology.distance_transform_edt(memory_array) * cell_size

    nodata = raster_utils.get_nodata_from_uri(dataset_in_uri)
    raster_utils.new_raster_from_base_uri(dataset_in_uri, dataset_out_uri, 'GTiff', nodata, gdal.GDT_Float32)

    dataset_out = gdal.Open(dataset_out_uri, 1)
    band = dataset_out.GetRasterBand(1)
    band.WriteArray(memory_array)

    band = None
    dataset_out = None


shapeTypes= {0: "Null Shape", 1: "Point", 3: "PolyLine", 5: "Polygon",
             8: "MultiPoint", 11: "PointZ", 13: "PolyLineZ",
             15: "PolygonZ", 18: "MultiPointZ", 21: "PointM",
             23: "PolyLineM", 25: "PolygonM", 28: "MultiPointM",
             31: "MultiPatch"}

def get_geometry_type_from_uri(datasource_uri):
    datasource = open(datasource_uri, 'r')
    datasource.seek(32)
    shape_type ,= struct.unpack('<i',datasource.read(4))
    datasource.close()

    return shape_type

def execute(args):
    ###
    #overiding, non-standard field names
    ###

    #transition fields
    args["transition_id"] = "ID"
    args["percent_field"] = "Percent Change"
    args["area_field"] = "Area Change"
    args["priority_field"] = "Priority"
    args["proximity_field"] = "Proximity"

    #factors fields
    args["suitability_id"] =  "ID"
    args["suitability_layer"] = "Layer"
    args["suitability_field"] = "Suitfield"
    args["distance_field"] = "Dist"
    
    ###
    #get parameters, set outputs
    ###
    workspace = args["workspace_dir"]
    landcover_uri = args["landcover"]
    override_uri = args["override"]

    landcover_resample_uri = os.path.join(workspace, "resample.tif")

    landcover_transition_uri = os.path.join(workspace,"transitioned.tif")
    override_dataset_uri = os.path.join(workspace,"override.tif")
    landcover_htm_uri = os.path.join(workspace,"landcover.htm")

    raster_utils.create_directories([workspace])

    ###
    #validate data
    ###

    #raise warning if nothing going to happen, ie no criteria provided

    #suitiblity validation
    #if polygon no distance field allowed
    #if point or line, integer distance field only

    ###
    #resample, align and rasterize data
    ###

    if args["resolution"] != "":
       if args["resolution"] < raster_utils.get_cell_size_from_uri(landcover_uri):
          msg = "The analysis resolution cannot be smaller than the input."
          LOGGER.error(msg)
          raise ValueError, msg

       else:
          LOGGER.info("Resampling land cover.")
          #gdal.GRA_Mode might be a better resample method, but requires GDAL >= 1.10.0
          raster_utils.resample_dataset(landcover_uri, args["resolution"], landcover_resample_uri, gdal.GRA_NearestNeighbour)
          landcover_uri = landcover_resample_uri

    cell_size = raster_utils.get_cell_size_from_uri(landcover_uri)
    if args["factors"]:
        factor_dict = raster_utils.get_lookup_from_csv(args["suitability"], args["suitability_id"])
        raster_format = "GTiff"
        factor_set = set()
        factor_folder = args["suitability_folder"]

        if args["factor_inclusion"]:
           option_list=["ALL_TOUCHED=TRUE"]
        else:
           option_list = ["ALL_TOUCHED=FALSE"]


        for factor_id in factor_dict:
            factor = factor_dict[factor_id][args["suitability_layer"]]
            factor_stem, _ = os.path.splitext(factor)
            suitability_field_name = factor_dict[factor_id][args["suitability_field"]]
            distance = factor_dict[factor_id][args["distance_field"]]
            LOGGER.debug("Found reference to factor (%s, %s, %s).", factor_stem, suitability_field_name, distance)
            if not (factor_stem, suitability_field_name, distance) in factor_set:
                factor_uri = os.path.join(factor_folder, factor)
                if not os.path.exists(factor_uri):
                   msg = "Missing file %s." % factor_uri
                   LOGGER.error(msg)
                   raise ValueError, msg

                shape_type = get_geometry_type_from_uri(factor_uri)
                LOGGER.debug("Processing %s.", shapeTypes[shape_type])
                
                if shape_type in [5, 15, 25, 31]: #polygon
                   LOGGER.info("Rasterizing %s using sutibility field %s.", factor_stem, suitability_field_name)
                   ds_uri = os.path.join(workspace, "%s_%s.tif" % (factor_stem, suitability_field_name))
                   nodata = 0
                   burn_value = [0]
                   suitability_field = ["ATTRIBUTE=%s" % suitability_field_name]
                   gdal_format = gdal.GDT_Float64
                   raster_utils.new_raster_from_base_uri(landcover_uri, ds_uri, raster_format, nodata, gdal_format)
                   raster_utils.rasterize_layer_uri(ds_uri, factor_uri, burn_value, option_list=option_list + suitability_field)

                elif shape_type in [1, 3, 8, 11, 13, 18, 21, 23, 28]: #point or line
                   distance = int(distance)
                   ds_uri = raster_utils.temporary_filename()
                   nodata = 1
                   burn_value = [0]
                   LOGGER.info("Rasterizing %s using distance field.", factor_stem)
                   gdal_format = gdal.GDT_Byte
                   raster_utils.new_raster_from_base_uri(landcover_uri, ds_uri, raster_format, nodata, gdal_format)

                   raster_utils.rasterize_layer_uri(ds_uri, factor_uri, burn_value, option_list)

                   distance_uri = raster_utils.temporary_filename()
                   fdistance_uri = os.path.join(workspace, "%s_%i.tif" % (factor_stem, distance))
                   calculate_distance_raster_uri(ds_uri, distance_uri)

                   nodata = -1
                   def threshold(value):
                       if value == nodata or value > distance:
                           return nodata
                       return value

                   raster_utils.vectorize_datasets([distance_uri],
                                                   threshold,
                                                   fdistance_uri,
                                                   raster_utils.get_datatype_from_uri(distance_uri),
                                                   nodata,
                                                   cell_size,
                                                   "union")

                else:
                   raise ValueError, "Invalid geometry type %i." % shape_type

                factor_set.add((factor_stem, suitability_field_name, distance))
            else:
               LOGGER.debug("Skipping already processed suitability layer.")

##    #select pixels
##    pixel_heap = disk_sort.sort_to_disk(distance_uri, 0)
##    ds = gdal.Open(ds_uri)
##
##    n_cols = ds.RasterXSize
##    n_rows = ds.RasterYSize
##    ds = None
##
##    dst_ds = gdal.Open(distance_uri, 1)
##    dst_band = dst_ds.GetRasterBand(1)
##
##    for n, (value, flat_index, dataset_index) in enumerate(pixel_heap):
##        if n == 10:
##           break
##        dst_band.WriteBlock(flat_index % n_cols, flat_index / n_cols, nodata, 1)
##
##    dst_band = None
##    dst_ds = None

    return


    ###
    #compute intermediate data if needed
    ###

    #contraints raster (reclass using permability values, filters on clump size)

    #normalize probabilities to be on a 10 point scale
    #probability raster (reclass using probability matrix)

    #proximity raster (gaussian for each landcover type, using max distance)
    #InVEST 2 uses 4-connectedness?

    #combine rasters for weighting into sutibility raster, multiply proximity by 0.3
    #[suitability * (1-factor weight)] + (factors * factor weight) or only single raster

    ###
    #reallocate pixels (disk heap sort, randomly reassign equal value pixels, applied in order)
    ###

    #reallocate
    src_ds = gdal.Open(landcover_uri)
    driver = gdal.GetDriverByName("GTiff")
    LOGGER.debug("Copying landcover to %s.", landcover_transition_uri)
    driver.CreateCopy(landcover_transition_uri, src_ds, 0 )
    src_ds = None

    #apply override
    field = args["override_field"]
    LOGGER.info("Overriding pixels using values from field %s.", field)
    datasource = ogr.Open(override_uri)
    layer = datasource.GetLayer()
    dataset = gdal.Open(landcover_transition_uri, 1)

    if dataset == None:
        msg = "Could not open landcover transition raster."
        LOGGER.error(msg)
        raise IOError, msg

    if datasource == None:
        msg = "Could not open override vector."
        LOGGER.error(msg)
        raise IOError, msg

    if not bool(args["override_inclusion"]):
        LOGGER.debug("Overriding all touched pixels.")
        options = ["ALL_TOUCHED=TRUE", "ATTRIBUTE=%s" % field]
    else:
        LOGGER.debug("Overriding only pixels with covered center points.")
        options = ["ATTRIBUTE=%s" % field]
    gdal.RasterizeLayer(dataset, [1], layer, options=options)
    dataset.FlushCache()
    datasource = None
    dataset = None

    ###
    #tabulate coverages
    ###
    htm = open(landcover_htm_uri,'w')
    htm.write("<html>")

    LOGGER.debug("Tabulating %s.", landcover_uri)
    landcover_counts = raster_utils.unique_raster_values_count(landcover_uri)

    LOGGER.debug("Tabulating %s.", landcover_transition_uri)
    landcover_transition_counts = raster_utils.unique_raster_values_count(
        landcover_transition_uri)

    for k in landcover_transition_counts:
        if k not in landcover_counts:
            landcover_counts[k]=0

    for k in landcover_counts:
        if k not in landcover_transition_counts:
            landcover_transition_counts[k]=0

    landcover_keys = landcover_counts.keys()
    landcover_keys.sort()

    htm.write("Land Use Land Cover")
    htm.write("<table border = \"1\">")
    htm.write("<tr><td>Type</td><td>Initial Count</td><td>Final Count</td><td>Difference</td></tr>")
    for k in landcover_keys:
        htm.write("<tr><td>%i</td><td>%i</td><td>%i</td><td>%i</td></tr>" % (k, landcover_counts[k], landcover_transition_counts[k], landcover_transition_counts[k] - landcover_counts[k]))
    htm.write("</table>")

    htm.write("</html>")
    htm.close()
