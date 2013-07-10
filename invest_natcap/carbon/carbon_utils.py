"""Useful functions for the carbon biophysical and valuation models."""

from osgeo import gdal
import numpy

from invest_natcap import raster_utils

def sum_pixel_values_from_uri(uri):
    dataset = gdal.Open(uri)
    band, nodata = raster_utils.extract_band_and_nodata(dataset)
    total_sum = 0.0
    # Loop over each row in out_band
    for row_index in range(band.YSize):
        row_array = band.ReadAsArray(0, row_index, band.XSize, 1)
        total_sum += numpy.sum(row_array[row_array != nodata])
    return total_sum

