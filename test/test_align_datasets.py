"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core

LOGGER = logging.getLogger('invest_core')

class TestRasterUtils(unittest.TestCase):
    def test_align_datasets(self):
        base_dir = 'data/test_out/align_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dataset_in_uris = ['data/align_datasets_data/flow_direction.tif',
                           'data/align_datasets_data/sed_ret_eff.tif',
                           'data/align_datasets_data/usle.tif']

        dataset_out_uris = ['data/test_out/align_datasets/' + x.split('/')[-1] for x in dataset_in_uris]

        datasets = [gdal.Open(x) for x in dataset_in_uris]
        dataset_list = raster_utils.align_datasets(datasets, dataset_out_uris)
