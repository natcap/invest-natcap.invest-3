import numpy 
import tables
import gdal

from invest_natcap import raster_utils

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
        for row_index in xrange(ds.RasterYSize):
            user_args[id][row_index,:] = band.ReadAsArray(0, row_index, ds.RasterXSize, 1)[0]
        
    out = h5file.createCArray(
        root, 'out', tables.Int32Atom(), shape=(ds.RasterYSize,ds.RasterXSize))
        
    expr = tables.Expr(operation, uservars=user_args)
    expr.set_output(out)
    expr.eval()

    raster_utils.new_raster_from_base_uri(
        ds_args.values()[0], ds_out, 'GTiff', -1, gdal.GDT_Int32)
    ds = gdal.Open(ds_out, gdal.GA_Update)
    band = ds.GetRasterBand(1)
    
    for row_index in xrange(ds.RasterYSize):
        band.WriteArray(out[row_index,:].reshape((1,ds.RasterXSize)), 0, row_index)