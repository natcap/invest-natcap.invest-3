import numpy
import tables
import gdal
import time

import pytable_tracer_cython
from invest_natcap import raster_utils

ds_args = {
    'ds1': './test/invest-data/test/data/base_data/terrestrial/lulc_samp_cur',
    'ds2': './test/invest-data/test/data/base_data/terrestrial/lulc_samp_fut',
    }
out_uri = './out.tif'


def calc_it(ds_args, ds_out, operation):
    h5_filename = raster_utils.temporary_filename()
    h5file = tables.openFile(h5_filename, mode='w', title="calc_it data")
    root = h5file.root
    
    ds = gdal.Open(ds_args.values()[0])
    
    user_args = {}
    
    for id, uri in ds_args.iteritems():
        user_args[id] = h5file.createCArray(
            root, id, tables.Int32Atom(), shape=(ds.RasterYSize,ds.RasterXSize))
            
        ds = gdal.Open(uri)
        band = ds.GetRasterBand(1)
        for row_index in range(ds.RasterYSize):
            user_args[id][row_index,:] = band.ReadAsArray(0, row_index, ds.RasterXSize, 1)[0]
        
    out = h5file.createCArray(
        root, 'out', tables.Int32Atom(), shape=(ds.RasterYSize,ds.RasterXSize))

    n_rows = ds.RasterYSize
    n_cols = ds.RasterXSize
    
    #for row_index in range(n_rows):
    #    row = user_args['ds1'][row_index,:]
    #    for col_index in range(n_cols):
    #        row[col_index] = row[col_index]**2
    #    out[row_index,:] = row
    expr = tables.Expr(operation, uservars=user_args)
    expr.set_output(out)
    expr.eval()

    raster_utils.new_raster_from_base_uri(
        ds_args.values()[0], ds_out, 'GTiff', -1, gdal.GDT_Int32)
    ds = gdal.Open(ds_out, gdal.GA_Update)
    band = ds.GetRasterBand(1)
    
    for row_index in xrange(ds.RasterYSize):
        band.WriteArray(out[row_index,:].reshape((1,ds.RasterXSize)), 0, row_index)

start = time.clock()
pytable_tracer_cython.calc_it(ds_args, out_uri, 'where((ds1==255) | (ds2==255), -1, ds1 + ds2)')
end = time.clock() - start
print "%f seconds" % end

start = time.clock()
calc_it(ds_args, out_uri, 'where((ds1==255) | (ds2==255), -1, ds1 + ds2)')
end = time.clock() - start
print "%f seconds" % end


# ds1 = gdal.Open('./test/invest-data/test/data/base_data/terrestrial/lulc_samp_cur')
# ds2 = gdal.Open('./test/invest-data/test/data/base_data/terrestrial/lulc_samp_fut')

# ndim = 20000
# h5file = tb.openFile('test.h5', mode='w', title="Test Array")
# root = h5file.root
# a = h5file.createCArray(root,'a',tb.Float64Atom(),shape=(ndim,ndim))
# a[:100,:100] = np.random.random(size=(100,100)) # Now put in some data

# expr = tb.Expr("a * a")

# out = h5file.createCArray(root,'out',tb.Float64Atom(),shape=(ndim,ndim))
# expr.set_output(out, append_mode=False)
# expr.eval()
# print out[:100,:100]

# h5file.close()