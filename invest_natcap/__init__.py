from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen
import pkg_resources

def log_model(model_name):
    """Submit a POST request to the defined URL with the modelname passed in as
    input.  The InVEST version number is also submitted, retrieved from the
    package's resources.

        model_name - a python string of the package version.

    returns nothing."""

    try:
        release_num = pkg_resources.require("invest_natcap")[0].version
    except pkg_resources.DistributionNotFound:
        # This exception is thrown when a model is run without being installed
        # through distutils.
        release_num = 'development'

    path = 'http://localhost/~jadoug06/test_ownership/server.php'
    data = {'model_name': model_name,
            'invest_release': release_num}
    try:
        urlopen(Request(path, urlencode(data)))
    except:
        # An exception was thrown, we don't care.
        pass

