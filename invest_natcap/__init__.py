from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen
import platform
import sys

#The following line of code hides some errors that seem important and doesn't
#raise exceptions on them.  FOr example:
#ERROR 5: Access window out of range in RasterIO().  Requested
#(1,15) of size 25x3 on raster of 26x17.
#disappears when this line is turned on.  Probably not a good idea to uncomment
#until we know what's happening
#from osgeo import gdal
#gdal.UseExceptions()

# This should be left as 'dev' unless BUILDING A RELEASE.
__version__ = 'dev'
if __version__ == 'dev':
    import datetime
    #Name the version based on the time it was built.
    #get rid of the colons in the time
    __version__ = 'dev_r'+datetime.datetime.now().isoformat('_').replace(':','_')


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

