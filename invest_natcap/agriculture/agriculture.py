import scipy.io.netcdf

import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('agriculture')

def netcdf_info_uri(uri):
    f = scipy.io.netcdf.netcdf_file(uri, 'r')

    for k in f.variables.keys():
        if k in f.dimensions.keys():
            LOGGER.debug("NetCDF contains variable %s of dimension %s.", k, f.dimensions[k])
        else:
            LOGGER.debug("NetCDF contains variable %s of shape %s.", k, f.variables[k].shape)
            
    f.close()
