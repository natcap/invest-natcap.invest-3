"""Useful functions for the carbon biophysical and valuation models."""

import os

from osgeo import gdal
import numpy

from invest_natcap import raster_utils

def make_suffix(model_args):
    try:
        file_suffix = model_args['suffix']
        if not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
    return file_suffix


def setup_dirs(workspace_dir, *dirnames):
    dirs = {name: os.path.join(workspace_dir, name) for name in dirnames}
    for new_dir in dirs.values():
        if not os.path.exists(new_dir):
            LOGGER.debug('Creating directory %s', output_directory)
            os.makedirs(new_dir)
    if len(dirs) == 1:
        return dirs.values()[0]
    return dirs


def sum_pixel_values_from_uri(uri):
    dataset = gdal.Open(uri)
    band, nodata = raster_utils.extract_band_and_nodata(dataset)
    total_sum = 0.0
    # Loop over each row in out_band
    for row_index in range(band.YSize):
        row_array = band.ReadAsArray(0, row_index, band.XSize, 1)
        total_sum += numpy.sum(row_array[row_array != nodata])
    return total_sum

