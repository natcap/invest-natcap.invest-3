import numpy as np
import tables as tb
import gdal

ds1 = gdal.Open('./test/invest-data/test/data/base_data/terrestrial/lulc_samp_cur')
ds2 = gdal.Open('./test/invest-data/test/data/base_data/terrestrial/lulc_samp_fut')

ndim = 20000
h5file = tb.openFile('test.h5', mode='w', title="Test Array")
root = h5file.root
a = h5file.createCArray(root,'a',tb.Float64Atom(),shape=(ndim,ndim))
a[:100,:100] = np.random.random(size=(100,100)) # Now put in some data

expr = tb.Expr("a * a")

out = h5file.createCArray(root,'out',tb.Float64Atom(),shape=(ndim,ndim))
expr.set_output(out, append_mode=False)
expr.eval()
print out[:100,:100]

h5file.close()