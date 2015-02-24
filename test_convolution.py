"""Tracer code for building nodata ignore funcitonality into convolve2d"""

import os
import subprocess

from invest_natcap import raster_utils
from invest_natcap.habitat_quality import habitat_quality

def test_it():
    """Entry point for the test"""

    signal_uri = (
        r"C:\Users\rich\Documents\Dropbox\hq_convolve_nodata\AGRICULTURE_c.tif")
    dr_pixel = 100

    kernel_uri = (
        r"C:\Users\rich\Documents\convolution_test_delete_this\kernel.tif")
    output_uri = (
        r"C:\Users\rich\Documents\convolution_test_delete_this\filtered.tif")
    raster_utils.create_directories([os.path.dirname(output_uri)])

    habitat_quality.make_linear_decay_kernel_uri(dr_pixel, kernel_uri)
    raster_utils.convolve_2d_uri(signal_uri, kernel_uri, output_uri)

    subprocess.Popen(
        [r"C:\Program Files\QGIS Brighton\bin\qgis.bat", output_uri])


if __name__ == '__main__':
    test_it()

