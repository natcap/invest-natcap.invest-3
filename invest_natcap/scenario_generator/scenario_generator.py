import os

from osgeo import gdal, ogr

from invest_natcap import raster_utils

from scipy import stats
from scipy.linalg import eig

from decimal import Decimal
from fractions import Fraction

import numpy

import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('scenario_generator')

def unique_raster_values_count(dataset):
    """Returns a list of the unique integer values on the given dataset

        dataset - a gdal dataset of some integer type

        returns a list of dataset's unique non-nodata values"""

    band = dataset.GetRasterBand(1)
    n_rows = band.YSize

    itemfreq = {}

    for row_index in xrange(n_rows):
        array = band.ReadAsArray(0, row_index, band.XSize, 1)[0]
        #numpy.bincount(array) would be better if all non-negative ints
        for v,n in stats.itemfreq(array):
            if v in itemfreq:
                itemfreq[int(v)]+=int(n)
            else:
                itemfreq[int(v)]=int(n)
        
    return itemfreq

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

def execute(args):

    ###
    #get parameters, set outputs
    ###
    workspace = args["workspace_dir"]
    landcover_uri = args["landcover"]
    override_uri = args["override"]
    
    landcover_transition_uri = os.path.join(workspace,"transitioned.tif")
    override_dataset_uri = os.path.join(workspace,"override.tif")
    landcover_htm_uri = os.path.join(workspace,"landcover.htm")

    raster_utils.create_directories([workspace])
    ###
    #validate data
    ###

    #raise warning if nothing going to happen, ie no criteria provided

    ###
    #resample, align and rasterize data
    ###
    
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
    dst_ds = driver.CreateCopy(landcover_transition_uri, src_ds, 0 )
    dst_ds = None
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
    
    src_ds = gdal.Open(landcover_uri)
    LOGGER.debug("Tabulating %s.", landcover_transition_uri)
    landcover_counts = unique_raster_values_count(src_ds)
    dst_ds = None
    src_ds = None

    src_ds = gdal.Open(landcover_transition_uri)
    LOGGER.debug("Tabulating %s.", landcover_transition_uri)
    landcover_transition_counts = unique_raster_values_count(src_ds)
    dst_ds = None
    src_ds = None

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
