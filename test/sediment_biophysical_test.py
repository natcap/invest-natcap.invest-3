"""URI level tests for the carbon biophysical module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest

from invest_natcap import postprocessing
from invest_natcap.sediment import sediment_biophysical
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('sediment_biophysical_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestSedimentBiophysical(unittest.TestCase):
    """Main testing class for the biophysical sediment tests"""
    def test_sediment_biophysical_re(self):
        """Test for sediment_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        base_dir = './data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % base_dir
        args['erosivity_uri'] = '%s/erosivity' % base_dir
        args['erodibility_uri'] = '%s/erodibility.tif' % base_dir
        args['landuse_uri'] = '%s/landuse_90.tif' % base_dir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % base_dir
        args['subwatersheds_uri'] = '%s/subwatersheds.shp' % base_dir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % base_dir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % base_dir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % base_dir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        sediment_biophysical.execute(args)
        postprocessing.plot_flow_direction(args['workspace_dir'] + os.sep +
            'Intermediate' + os.sep + 'flow.tif',
            args['workspace_dir'] + os.sep + 'Intermediate' + os.sep +
            'flow_arrows.png')

    def test_postprocessing_flow_direction(self):
        """Test for sediment_biophysical function running with sample input to \
            do sequestration and harvested wood products on lulc maps."""
        raise SkipTest
        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        postprocessing.plot_flow_direction(args['workspace_dir'] + os.sep +
            'Intermediate' + os.sep + 'flow.tif',
            args['workspace_dir'] + os.sep + 'Intermediate' + os.sep +
            'flow_arrows.png')
