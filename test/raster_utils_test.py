from osgeo import gdal

import invest_test_core
import raster_utils

ds=gdal.Open('/home/rpsharp/local/workspace/invest-natcap.water-funds/data/monterrey_data/UPSLOPESOURCE.TIF_clip.tif')

invest_test_core.make_random_raster_from_base(ds,1,30,'./random_lulc.tif')

ds_random = gdal.Open('./random_lulc.tif')
raster_utils.calculate_raster_stats(ds_random)
