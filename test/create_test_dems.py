from osgeo import gdal

import invest_test_core
import invest_cython_core
from invest_natcap import raster_utils

points = {
    (0.0,0.0): 50,
    (0.0,1.0): 100,
    (1.0,0.0): 90,
    (1.0,1.0): 0,
    (0.5,0.5): 45}

points_down = {
    (0.0,0.0): 100,
    (0.0,1.0): 100,
    (1.0,0.0): 0,
    (1.0,1.0): 0}


dem = invest_test_core.make_sample_dem(100,100,points_down, 0.0, -1, 'random_dem.tif')

flow_dataset = raster_utils.new_raster_from_base(dem, 'random_dem_flow.tif', 'GTiff',
                                                 -1, gdal.GDT_Float32)

invest_cython_core.flow_direction_inf(dem, [0, 0, 100, 100], flow_dataset)
raster_utils.calculate_raster_stats(dem)
raster_utils.calculate_raster_stats(flow_dataset)
