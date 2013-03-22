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
    def test_malaria_re(self):
        """Test for sediment function running with default InVEST 
           sample input."""
        args = {}
        args['workspace_dir'] = './data/test_out/malaria_output'
        base_dir = './data/malaria_test_data'
        args['dem_uri'] = 'data/sediment_test_data/dem'
        args['lulc_uri'] = 'data/sediment_test_data/landuse_90.tif'
        args['max_vector_flight'] = 150.0
        args['population_uri'] = 'empty.tif'
        args['breeding_suitability_table_uri'] = os.path.join(base_dir,'breeding_suitability_table.csv')

        malaria.execute_30(**args)
