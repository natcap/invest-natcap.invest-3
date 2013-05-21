
import os

from invest_natcap import raster_utils

class FileNotFound(Exception):
    pass

class DataManager(object):
    def collect_parameters(self, parameters):
        temp_workspace = raster_utils.temporary_folder()

        new_args = {}

        # Recurse through the parameters to locate any URIs
        #   If a URI is found, copy that file to a new location in the temp
        #   workspace and update the URI reference.
        #   Duplicate URIs should also have the same replacement URI.
        for key, value in parameters.iteritems():
            try:
                if os.path.exists(value):
                    new_filename = os.path.basename(value)
                    new_args[key] = new_filename
                    shutil.copyfile(value, os.path.join(temp_workspace,
                        new_filename))
            except TypeError:
                # When the value is not a string.
                new_args[key] = value

        # write parameters to a new json file in the temp workspace

