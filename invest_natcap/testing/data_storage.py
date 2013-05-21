
import os
import json
import tarfile

from invest_natcap import raster_utils

class FileNotFound(Exception):
    pass

class DataManager(object):
    def collect_parameters(self, parameters, archive_uri):
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
        param_file_uri = os.path.join(temp_workspace, 'parameters.json')
        parameter_file = open(param_file_uri, mode='w+')
        parameter_file.writelines(json.dumps(new_args))
        parameter_file.close()

        # archive the workspace.
        shutil.make_archive(archive_uri, 'gztar', root_dir=temp_workspace,
            base_dir=temp_workspace)

    def extract_archive(self, workspace_dir, archive_uri):
        # Extract the archive to the workspace_dir and return the arguments
        # dictionary.
        # workspace_dir must be empty.

        # extract the archive to the workspace
        archive = tarfile.open(archive_uri)
        archive.extractall(workspace_dir)
        archive.close()

        # get the arguments dictionary
        return json.load(open(os.path.join(workspace_dir, 'parameters.json')))


