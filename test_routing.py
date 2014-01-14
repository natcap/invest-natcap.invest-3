import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap.routing import routing_utils
import routing_cython_core

import pyximport
pyximport.install()

#base_uri = 'regression_claybark_flux_out.tif'
base_uri = 'regression_willamate_flux_out.tif'
#base_uri = 'regression_10x10_flux_out.tif'
#out_uri = 'claybark_flux_out.tif'
out_uri = 'willamate_flux_out.tif'
#out_uri = '10x10_flux_out.tif'
#dem_uri = './test/invest-data/Base_Data/Marine/DEMs/claybark_dem'
dem_uri = './test/invest-data/Base_Data/Freshwater/dem'
#dem_uri = './test_input_10x10/test_dem_10x10.tif'

dem_offset_uri = './offset_dem.tif'

start = time.time()
#routing_utils.flow_accumulation('./test_input_10x10/test_dem_10x10.tif', out_uri)
#cProfile.runctx('routing_cython_core.resolve_flat_regions_for_drainage(dem_uri, dem_offset_uri)', globals(), locals(), 'flowstats')
cProfile.run('routing_utils.flow_accumulation(dem_uri, out_uri)', 'flowstats')
p = pstats.Stats('flowstats')
p.sort_stats('time').print_stats(10)
p.sort_stats('cumulative').print_stats(10)
end = time.time()

#print 'total time ', end-start, 's'


base_ds = gdal.Open(base_uri)
out_ds = gdal.Open(out_uri)
base_band = base_ds.GetRasterBand(1)
out_band = out_ds.GetRasterBand(1)

base_array = base_band.ReadAsArray()
out_array = out_band.ReadAsArray()

numpy.testing.assert_array_almost_equal(base_array, out_array)
