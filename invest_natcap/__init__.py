from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen

# This should be left as 'development' unless programmatically set when building
# a release.  DO NOT ALTER THIS VERSION BY HAND.
__version__ = 'development'

def log_model(model_name, model_version=None):
    """Submit a POST request to the defined URL with the modelname passed in as
    input.  The InVEST version number is also submitted, retrieved from the
    package's resources.

        model_name - a python string of the package version.
        model_version=None - a python string of the model's version.  Defaults
            to None if a model version is not provided.

    returns nothing."""

    path = 'http://ncp-dev.stanford.edu/~invest-logger/log-modelname.php'
    data = {'model_name': model_name,
            'invest_release': __version__}

    if model_version == None:
        model_version = __version__
    data['model_version'] = model_version

    try:
        urlopen(Request(path, urlencode(data)))
    except:
        # An exception was thrown, we don't care.
        pass

