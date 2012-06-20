from osgeo import gdal

import invest_natcap.raster_utils

dataset = gdal.Open('./data/hydropower_regression_data/sub_shed_mask.tif')
rules = {1: 50.2, 2: -1838, 3: 0.1}
output_uri = './data/test_out/reclassified_raster.tif'

nodata = -1.0e-30
datatype = gdal.GDT_Float32

invest_natcap.raster_utils.reclassify_by_dictionary(dataset,rules,output_uri,'MEM', nodata,datatype)

rules = {1: 10, 2: 20, 3: 30}
output_uri = './data/test_out/reclassified_raster_byte.tif'

nodata = 0
datatype = gdal.GDT_Byte

invest_natcap.raster_utils.reclassify_by_dictionary(dataset,rules,output_uri,'GTiff',nodata,datatype)
