from numpy import *
try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric


def execute(args):
  #args is a dictionary
  #GDAL URI is handled before this function is called, so GDAL object should be passed with args
  #carbon pool should have been processed from its file into a dictionary, passed with args
  #output file URI should also have been passed with args
  #The purpose of this function is to assemble calls to the various carbon components into a conhesive result

  #convert the passed GDAL object to a 2D array
  gdalObj = args['lulc'].GetRasterBand(1)
  cols = args['lulc'].RasterXSize
  rows = args['lulc'].RasterYSize
  lulc = gdalObj.ReadAsArray(0, 0, cols, rows)

  #get the carbon pools
  pools = args['carbon_pool']

  #initialize an output array
  #it's the same dimensions as the lulc
  output = zeros(lulc.shape)

  carbon_seq(lulc, pools, output)

