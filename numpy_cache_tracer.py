import numpy
import gdal

from invest_natcap import raster_utils

dem_uri = './test/invest-data/Base_Data/Freshwater/dem'
out_uri = 'out.tif'

nodata_value = raster_utils.get_nodata_from_uri(dem_uri)

raster_utils.new_raster_from_base_uri(
    dem_uri, out_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
    INF)


dem_ds = gdal.Open(dem_uri)
dem_band = dem_ds.GetRasterBand(1)

n_cols = dem_ds.RasterXSize
n_rows = dem_ds.RasterYSize

cache_rows = 10

cache_data_array = numpy.empty((cache_rows, 1, n_cols), dtype=numpy.float)
cache_tag_array = numpy.empty((cache_rows,), dtype=numpy.int)
cache_tag_array[:] = -1
cache_dirty_array = numpy.empty((cache_rows,), dtype=numpy.byte)
cache_dirty_array[:] = 0

for row_index in xrange(30):
    print cache_tag_array
    for row_offset in xrange(3):
        offset_row_index = row_index + row_offset

        if offset_row_index < 0 or offset_row_index >= n_rows:
            continue

        cache_tag = offset_row_index / cache_rows
        cache_index = offset_row_index % cache_rows

        if (cache_tag_array[cache_index] != cache_tag):
            if cache_dirty_array[cache_index] and cache_tag_array[cache_index] != -1:
                print 'write back cache to row %d' % (cache_rows)
                dem_band.WriteArray(
                    cache_data_array[cache_index], xoff=0, yoff=cache_rows)
                cache_dirty_array[cache_index] = 0

            if cache_tag_array[cache_index] != -1:
                print 'unloading row %d' % (cache_index + cache_tag_array[cache_index] * cache_rows)
            cache_tag_array[cache_index] = cache_tag
            dem_band.ReadAsArray(
                xoff=0, yoff=offset_row_index,
                win_xsize=n_cols, win_ysize=1, buf_obj=cache_data_array[cache_index])
        else:
            print "we've got row %d loaded" % (offset_row_index)
