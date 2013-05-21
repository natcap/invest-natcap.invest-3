
from invest_natcap import raster_utils

class DataManager(object):
    def collect_parameters(self, parameters):
        temp_workspace = raster_utils.temporary_folder()

        # Recurse through the parameters to locate any URIs
        #   If a URI is found, copy that file to a new location in the temp
        #   workspace and update the URI reference.
        #   Duplicate URIs should also have the same replacement URI.

        # write parameters to a new json file in the temp workspace

