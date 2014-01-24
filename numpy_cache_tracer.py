import numpy
import gdal

from invest_natcap import raster_utils

dem_uri = './test/invest-data/Base_Data/Freshwater/dem'
out_uri = 'out.tif'

from UserDict import DictMixin

class odict(DictMixin):
    
    def __init__(self):
        self._keys = []
        self._data = {}
        
        
    def __setitem__(self, key, value):
        if key not in self._data:
            self._keys.append(key)
        self._data[key] = value
        
        
    def __getitem__(self, key):
        return self._data[key]
    
    
    def __delitem__(self, key):
        del self._data[key]
        self._keys.remove(key)
        
        
    def keys(self):
        return list(self._keys)
    
    
    def copy(self):
        copyDict = odict()
        copyDict._data = self._data.copy()
        copyDict._keys = self._keys[:]
        return copyDict

    
nodata_value = raster_utils.get_nodata_from_uri(dem_uri)
raster_utils.new_raster_from_base_uri(
    dem_uri, out_uri, 'GTiff', nodata_value, gdal.GDT_Float32)

dem_ds = gdal.Open(dem_uri)
dem_band = dem_ds.GetRasterBand(1)

n_cols = dem_ds.RasterXSize
n_rows = dem_ds.RasterYSize

cache_rows = 10

row_cache = odict()

for row_index in xrange(30):
    print len(row_cache)
    for row_offset in xrange(3):
        offset_row_index = row_index + row_offset

        if offset_row_index < 0 or offset_row_index >= n_rows:
            continue
        if offset_row_index not in row_cache:
            if len(row_cache) >= cache_rows:
                #we need to bump something out of the cache
                cached_row_index, (row_data, cache_dirty) = row_cache.popitem()
                if cache_dirty:
                    print 'write back cache to row %d' % (cached_row_index)
                    dem_band.WriteArray(
                        row_data, xoff=0, yoff=cached_row_index)
            
            row_data = dem_band.ReadAsArray(
                xoff=0, yoff=offset_row_index, win_xsize=n_cols, win_ysize=1)
            print 'loading row %d' % offset_row_index
            row_cache[offset_row_index] = (row_data, False)
        else:
            print "we've got row %d loaded" % (offset_row_index)
