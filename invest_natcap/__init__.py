from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen

# This should be left as 'development' unless programmatically set when building
# a release.  DO NOT ALTER THIS VERSION BY HAND.
__version__ = '2.3.0a9'

def log_model(model_name):
    """Submit a POST request to the defined URL with the modelname passed in as
    input.  The InVEST version number is also submitted, retrieved from the
    package's resources.

        model_name - a python string of the package version.

    returns nothing."""

    path = 'http://ncp-dev.stanford.edu/~invest-logger/log-modelname.php'
    data = {'model_name': model_name,
            'invest_release': __version__}
    try:
        urlopen(Request(path, urlencode(data)))
    except:
        # An exception was thrown, we don't care.
        pass

