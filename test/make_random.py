import invest_test_core
from osgeo import gdal
ds=gdal.Open('/home/rpsharp/local/workspace/invest-natcap.water-funds/data/monterrey_data/UPSLOPESOURCE.TIF_clip.tif')
invest_test_core.make_random_raster_from_base(ds,1,30,'/home/rpsharp/local/workspace/invest-natcap.water-funds/data/monterrey_data/random_lulc.tif')
