"""
A module for InVEST test-related data storage.
"""

import os
import json
import tarfile
import shutil
import inspect
import logging
import tempfile
import string
import random

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils


DATA_ARCHIVES = os.path.join('data', 'regression_archives')
INPUT_ARCHIVES = os.path.join(DATA_ARCHIVES, 'input')
OUTPUT_ARCHIVES = os.path.join(DATA_ARCHIVES, 'output')

COMPLEX_FILES = {
    'ArcInfo Binary Grid': ['dblbnd.adf', 'hdr.adf', 'log', 'metadata.xml',
        'prj.adf', 'sta.adf', 'vat.adf', 'w001001.adf', 'w001001x.adf'],
    'ESRI Shapefile': ['.dbf', '.shp', '.prj', '.shx'],
}

LOGGER = logging.getLogger('data_storage')


def archive_uri(name=None):
    if name is None:
        calling_function = inspect.stack()[1]
        name = calling_function.__name__

    return(os.path.join(INPUT_ARCHIVE, name))

def is_multi_file(filename):
    """Check if the filename given is a file with multiple parts to it, such as
        an ESRI shapefile or an ArcInfo Binary Grid."""
    pass

def make_raster_dir(workspace, seed_string):
    random.seed(seed_string)
    new_dirname = ''.join(random.choice(string.ascii_uppercase + string.digits)
            for x in range(6))
    new_dirname = 'raster_' + new_dirname
    raster_dir = os.path.join(workspace, new_dirname)
    LOGGER.debug('new raster dir: %s', raster_dir)
    return raster_dir

def collect_parameters(parameters, archive_uri):
    """Collect an InVEST model's arguments into a dictionary and archive all
        the input data.

        parameters - a dictionary of arguments
        archive_uri - a URI to the target archive.

        Returns nothing."""

    temp_workspace = raster_utils.temporary_folder()

    def get_multi_part_gdal(filepath):
        if os.path.isdir(filepath):
            raster_dir = make_raster_dir(temp_workspace, os.path.basename(filepath))

            shutil.copytree(filepath, raster_dir)
            return os.path.basename(raster_dir)
        else:
            parent_folder = os.path.dirname(filepath)
            files_in_parent = glob.glob(os.path.join(parent_folder, '*.*'))
            raster_files = COMPLEX_FILES['ArcInfo Binary Grid']
            if len(files_in_parent) > len(raster_files):
                # create a new folder in the temp workspace
                raster_dir = make_raster_dir(temp_workspace)

                # copy all the raster files over to the new folder
                for raster_file in raster_files:
                    orig_raster_uri = os.path.join(parent_folder, raster_file)
                    new_raster_uri = os.path.join(raster_dir, raster_file)
                    shutil.copyfile(orig_raster_uri, new_raster_uri)

                # return the new folder
                return raster_dir
            else:
                # this folder only contains raster files.
                return parent_folder

    def get_multi_part_ogr(filepath):
        pass

    def get_multi_part(filepath):
        # If the user provides a mutli-part file, wrap it into a folder and grab
        # that instead of the individual file.
        if gdal.Open(filepath) != None:
            # file is a raster
            LOGGER.debug('%s is a raster', filepath)
            return get_multi_part_gdal(filepath)
        elif ogr.Open(filepath) != None:
            # file is a shapefile
            return get_multi_part_ogr(filepath)
        return None

    def get_if_file(parameter):
        try:
            multi_part_folder = get_multi_part(parameter)
            if multi_part_folder != None:
                return multi_part_folder
            elif os.path.isfile(parameter):
                new_filename = os.path.basename(parameter)
                shutil.copyfile(parameter, os.path.join(temp_workspace,
                    new_filename))
                return new_filename
            elif os.path.isdir(parameter):
                # parameter is a folder, so we want to copy the folder and all
                # its contents to temp_workspace.
                new_foldername = tempfile.mkdtemp(prefix='data_',
                    dir=temp_workspace)
                shutil.copytree(parameter, new_foldername)
                return new_foldername
            else:
                # Parameter does not exist on disk.  Print an error to the
                # logger and move on.
                LOGGER.error('File %s does not exist on disk.  Skipping.',
                    parameter)
        except TypeError:
            # When the value is not a string.
            pass
        return parameter

    def collect_list(parameter_list):
        new_list = []
        for parameter in parameter_list:
            new_list.append(types[parameter.__class__](parameter))
        return new_list

    def collect_dict(parameter_dict):
        new_dict = {}
        for key, value in parameter_dict.iteritems():
            new_dict[key] = types[value.__class__](value)
        return new_dict

    types = {
        list: collect_list,
        dict: collect_dict,
        str: get_if_file,
        unicode: get_if_file,
        int: lambda x: x,
        float: lambda x: x,
    }

    # Recurse through the parameters to locate any URIs
    #   If a URI is found, copy that file to a new location in the temp
    #   workspace and update the URI reference.
    #   Duplicate URIs should also have the same replacement URI.
    try:
        del parameters['workspace_dir']
    except:
        LOGGER.warn(('Parameters missing the workspace key \'workspace_dir\.'
            ' Be sure to check your archived data'))
    new_args = collect_dict(parameters)

    LOGGER.debug('new arguments: %s', new_args)
    # write parameters to a new json file in the temp workspace
    param_file_uri = os.path.join(temp_workspace, 'parameters.json')
    parameter_file = open(param_file_uri, mode='w+')
    parameter_file.writelines(json.dumps(new_args))
    parameter_file.close()

    # archive the workspace.
    shutil.make_archive(archive_uri, 'gztar', root_dir=temp_workspace,
        logger=LOGGER)


def extract_archive(workspace_dir, archive_uri):
    """Extract a .tar.gzipped file to the given workspace.

        workspace_dir - the folder to which the archive should be extracted
        archive_uri - the uri to the target archive

        Returns nothing."""

    archive = tarfile.open(archive_uri)
    archive.extractall(workspace_dir)
    archive.close()


def extract_parameters_archive(workspace_dir, archive_uri):
    """Extract the target archive to the target workspace folder.

        workspace_dir - a uri to a folder on disk.  Must be an empty folder.
        archive_uri - a uri to an archive to be unzipped on disk.  Archive must
            be in .tar.gz format.

        Returns a dictionary of the model's parameters for this run."""

    # extract the archive to the workspace
    extract_archive(workspace_dir, archive_uri)

    # get the arguments dictionary
    arguments_dict = json.load(open(os.path.join(workspace_dir, 'parameters.json')))

    def _get_if_uri(parameter):
        """If the parameter is a file, returns the filepath relative to the
        extracted workspace.  If the parameter is not a file, returns the
        original parameter."""
        try:
            temp_file_path = os.path.join(workspace_dir, parameter)
            if os.path.isfile(temp_file_path):
                return temp_file_path
        except TypeError:
            # When the parameter is not a string
            pass
        return parameter

    workspace_args = {}
    for key, value in arguments_dict.iteritems():
        workspace_args[key] = _get_if_uri(value)

    return workspace_args
