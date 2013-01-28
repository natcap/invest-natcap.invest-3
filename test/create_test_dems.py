import subprocess

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

points_right = {
    (0.0,0.0): 100,
    (0.0,1.0): 100,
    (1.0,0.0): 0,
    (1.0,1.0): 0}

points_down = {
    (0.0,0.0): 100,
    (0.0,1.0): 0,
    (1.0,0.0): 100,
    (1.0,1.0): 0}

points_up = {
    (0.0,0.0): 0,
    (0.0,1.0): 100,
    (1.0,0.0): 0,
    (1.0,1.0): 100}

points_left = {
    (0.0,0.0): 0,
    (0.0,1.0): 0,
    (1.0,0.0): 100,
    (1.0,1.0): 100}

n=50
dem = invest_test_core.make_sample_dem(n,n,points, 0.0, -1, 'random_dem.tif')

flow_dataset = raster_utils.new_raster_from_base(dem, 'random_dem_flow.tif', 'GTiff',
                                                 -1, gdal.GDT_Float32)

invest_cython_core.flow_direction_inf(dem, [0, 0, n, n], flow_dataset)

flow_dem_uri = 'random_dem_flow_accum.tif'
flow_accumulation_dataset = raster_utils.flow_accumulation_dinf(flow_dataset, dem, flow_dem_uri)

raster_utils.calculate_raster_stats(dem)
raster_utils.calculate_raster_stats(flow_dataset)
raster_utils.calculate_raster_stats(flow_accumulation_dataset)
