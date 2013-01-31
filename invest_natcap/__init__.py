from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen
import platform
import sys

import build_utils

#The following line of code hides some errors that seem important and doesn't
#raise exceptions on them.  FOr example:
#ERROR 5: Access window out of range in RasterIO().  Requested
#(1,15) of size 25x3 on raster of 26x17.
#disappears when this line is turned on.  Probably not a good idea to uncomment
#until we know what's happening
#from osgeo import gdal
#gdal.UseExceptions()

try:
    import invest_version
    __version__ = invest_version.release
    if __version__ == 'None':
        __version__ = invest_version.build_id
except (ImportError, AttributeError):
    __version__ = build_utils.invest_version()

def log_model(model_name, model_version=None):
    """Submit a POST request to the defined URL with the modelname passed in as
    input.  The InVEST version number is also submitted, retrieved from the
    package's resources.

        model_name - a python string of the package version.
        model_version=None - a python string of the model's version.  Defaults
            to None if a model version is not provided.

    returns nothing."""

    path = 'http://ncp-dev.stanford.edu/~invest-logger/log-modelname.php'
    data = {
        'model_name': model_name,
        'invest_release': __version__,
        'system': {
            'os': platform.system(),
            'release': platform.release(),
            'full_platform_string': platform.platform(),
            'fs_encoding': sys.getfilesystemencoding()
        }
    }

    if model_version == None:
        model_version = __version__
    data['model_version'] = model_version

    try:
        urlopen(Request(path, urlencode(data)))
    except:
        # An exception was thrown, we don't care.
        print 'an exception encountered when logging'
        pass

