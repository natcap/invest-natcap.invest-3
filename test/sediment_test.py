"""URI level tests for the sediment module"""

import unittest
import logging
import os
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.sediment import sediment
import invest_cython_core
import invest_test_core
from invest_natcap.sediment import sediment_core
from invest_natcap import raster_utils


LOGGER = logging.getLogger('sediment_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestSediment(unittest.TestCase):
    """Main testing class for the sediment tests"""
    def test_sediment_re(self):
        """Test for sediment function running with default InVEST 
           sample input."""
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/sediment_output'
#        args['suffix'] = None
        base_dir = './invest-data/test/data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % base_dir
        args['erosivity_uri'] = '%s/erosivity' % base_dir
        args['erodibility_uri'] = '%s/erodibility.tif' % base_dir
        args['landuse_uri'] = '%s/landuse_90.tif' % base_dir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % base_dir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % base_dir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % base_dir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % base_dir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        args['sediment_threshold_table_uri'] = os.path.join(base_dir, 'sediment_threshold_table.csv')
        args['sediment_valuation_table_uri'] = os.path.join(base_dir, 'sediment_valuation_table.csv')

        sediment.execute(args)

        output_shape = os.path.join(args['workspace_dir'],'Output', 'watershed_outputs.shp')
        regression_shape = os.path.join('data', 'sediment_regression_data', 'watershed_outputs.shp')
        invest_test_core.assertTwoShapesEqualURI(self, output_shape, regression_shape)
