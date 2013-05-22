"""
A module for InVEST test-related data storage.
"""

import os
import json
import tarfile
import shutil

from invest_natcap import raster_utils


DATA_ARCHIVES = os.path.join('data', 'regression_archives')
INPUT_ARCHIVES = os.path.join(DATA_ARCHIVES, 'input')
OUTPUT_ARCHIVES = os.path.join(DATA_ARCHIVES, 'output')

def collect_parameters(parameters, archive_uri):
    """Collect an InVEST model's arguments into a dictionary and archive all
        the input data.

        parameters - a dictionary of arguments
        archive_uri - a URI to the target archive.

        Returns nothing."""

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


def extract_archive(workspace_dir, archive_uri):
    """Extract the target archive to the target workspace folder.

        workspace_dir - a uri to a folder on disk.  Must be an empty folder.
        archive_uri - a uri to an archive to be unzipped on disk.  Archive must
            be in .tar.gz format.

        Returns a dictionary of the model's parameters for this run."""

    # extract the archive to the workspace
    archive = tarfile.open(archive_uri)
    archive.extractall(workspace_dir)
    archive.close()

    # get the arguments dictionary
    arguments_dict = json.load(open(os.path.join(workspace_dir, 'parameters.json')))

    workspace_args = {}
    for key, value in arguments_dict.iteritems():
        try:
            if os.path.relpath(value, workspace_dir):
                workspace_args[key] = os.path.join(workspace, value)
            else:
                workspace_args[key] = value
        except ValueError:
            workspace_args[key] = value

    return workspace_args
