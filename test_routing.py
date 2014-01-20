import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap.routing import routing_utils
import routing_cython_core

import pyximport
pyximport.install()

test = 'willamate'

if test == 'peru':
    base_uri = 'regression_peru_dem_out.tif'
    out_uri = 'peru_dem_out.tif'
    dem_uri = 'Peru_for_Rich/dem_50km'
    regression_dem_offset_uri = 'regression_peru_dem_offset.tif'
    dem_offset_uri = 'peru_dem_offset.tif'
if test == 'willamate':
    base_uri = 'regression_willamate_flux_out.tif'
    out_uri = 'willamate_flux_out.tif'
    dem_uri = './test/invest-data/Base_Data/Freshwater/dem'
    regression_dem_offset_uri = './regression_offset_willamate_flux_out.tif'
    dem_offset_uri = './offset_willamate_flux_out.tif'


#base_uri = 'regression_10x10_flux_out.tif'
#out_uri = '10x10_flux_out.tif'
#dem_uri = './test_input_10x10/test_dem_10x10.tif'
#regression_dem_offset_uri = 'regression_test_dem_10x10.tif'
#dem_offset_uri = 'offset_test_dem_10x10.tif'


start = time.time()
cProfile.runctx('routing_cython_core.resolve_flat_regions_for_drainage(dem_uri, dem_offset_uri)', globals(), locals(), 'flowstats')
#cProfile.run('routing_utils.flow_accumulation(dem_uri, out_uri)', 'flowstats')
p = pstats.Stats('flowstats')
p.sort_stats('time').print_stats(10)
p.sort_stats('cumulative').print_stats(10)
end = time.time()

#print 'total time ', end-start, 's'
regression_dem_offset_ds = gdal.Open(regression_dem_offset_uri)
regression_dem_offset_band = regression_dem_offset_ds.GetRasterBand(1)
regression_dem_offset_array = regression_dem_offset_band.ReadAsArray()
dem_offset_ds = gdal.Open(dem_offset_uri)
dem_offset_band = dem_offset_ds.GetRasterBand(1)
dem_offset_array = dem_offset_band.ReadAsArray()

numpy.testing.assert_array_almost_equal(regression_dem_offset_array, dem_offset_array)



base_ds = gdal.Open(base_uri)
out_ds = gdal.Open(out_uri)
base_band = base_ds.GetRasterBand(1)
out_band = out_ds.GetRasterBand(1)

base_array = base_band.ReadAsArray()
out_array = out_band.ReadAsArray()

numpy.testing.assert_array_almost_equal(base_array, out_array)
