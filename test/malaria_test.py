"""URI level tests for the sediment module"""

import unittest
import logging
import os
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.malaria import malaria
import invest_test_core
from invest_natcap import raster_utils


LOGGER = logging.getLogger('malaria_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestMalaria(unittest.TestCase):
    """Main testing class for the sediment tests"""

    def test_malaria_clip_reproject_re(self):
        original_dataset_uri = './invest-data/test/data/malaria_test_data/global_pop'
        base_dataset_uri = './invest-data/test/data/sediment_test_data/landuse_90.tif'
        pixel_size = 30.0
        os.makedirs('./invest-data/test/data/test_out/malaria_output/')
        output_uri = './invest-data/test/data/test_out/malaria_output/clipped_pop.tif'
#        malaria.reproject_and_clip_dataset_uri(
#            original_dataset_uri, base_dataset_uri, pixel_size, output_uri)


    def test_malaria_re(self):
        """Test for sediment function running with default InVEST 
           sample input."""
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/malaria_output'
        base_dir = './invest-data/test/data/malaria_test_data'
        args['dem_uri'] = './invest-data/test/data/sediment_test_data/dem'
        args['flow_threshold'] = 100
        args['lulc_uri'] = 'data/sediment_test_data/landuse_90.tif'
        args['max_vector_flight'] = 150.0
        args['population_uri'] = './invest-data/test/data/malaria_test_data/global_pop'

        args['breeding_suitability_table_uri'] = os.path.join(base_dir,'breeding_suitability_table.csv')
        args['area_to_convert'] = 2.0
        malaria.execute_30(**args)
