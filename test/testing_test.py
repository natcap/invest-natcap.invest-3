import unittest
import os

import invest_natcap.testing as testing
from invest_natcap.testing import data_storage
from invest_natcap import raster_utils

POLLINATION_DATA = os.path.join('data', 'pollination', 'samp_input')
CARBON_DATA = os.path.join('data', 'carbon', 'input')
REGRESSION_ARCHIVES = os.path.join('data', 'data_storage', 'regression')
TEST_INPUT = os.path.join('data', 'data_storage', 'test_input')
TEST_OUT = os.path.join('data', 'test_out')


class DataStorageTest(testing.GISTest):
    def test_collect_parameters_simple(self):
        params = {
            'a': 1,
            'b': 2,
            'c': os.path.join(POLLINATION_DATA, 'LU.csv'),
        }

        archive_uri = os.path.join(TEST_OUT, 'archive')

        data_storage.collect_parameters(params, archive_uri)
        archive_uri = archive_uri + '.tar.gz'

        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'collect_parameters_simple.tar.gz')

        self.assertArchive(archive_uri, regression_archive_uri)

    def test_collect_parameters_nested_dict(self):
        params = {
            'a': 1,
            'b': 2,
            'd': {
                'one': 1,
                'two': 2,
                'three': os.path.join(POLLINATION_DATA, 'Guild.csv')
            },
            'c': os.path.join(POLLINATION_DATA, 'LU.csv'),
        }

        archive_uri = os.path.join(TEST_OUT, 'archive_nested_dict')

        data_storage.collect_parameters(params, archive_uri)
        archive_uri = archive_uri + '.tar.gz'

        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'simple_nested_dict.tar.gz')

        self.assertArchive(archive_uri, regression_archive_uri)

    def test_archive_arc_raster_nice(self):
        params = {
            'raster': os.path.join('data', 'base_data', 'Freshwater', 'precip')
        }

        archive_uri = os.path.join(TEST_OUT, 'raster_nice')
        data_storage.collect_parameters(params, archive_uri)

        archive_uri += '.tar.gz'
        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'arc_raster_nice.tar.gz')
        self.assertArchive(archive_uri, regression_archive_uri)

    def test_archive_arc_raster_messy(self):
        params = {
            'raster': os.path.join(TEST_INPUT, 'messy_raster_organization',
                'hdr.adf')
        }

        archive_uri = os.path.join(TEST_OUT, 'raster_messy')
        data_storage.collect_parameters(params, archive_uri)

        archive_uri += '.tar.gz'
        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'arc_raster_messy.tar.gz')
        self.assertArchive(archive_uri, regression_archive_uri)

    def test_archive_esri_shapefile(self):
        params = {
            'vector': os.path.join(CARBON_DATA, 'harv_samp_cur.shp')
        }

        archive_uri = os.path.join(TEST_OUT, 'vector_collected')
        data_storage.collect_parameters(params, archive_uri)

        archive_uri += '.tar.gz'
        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'vector_collected.tar.gz')
        self.assertArchive(archive_uri, regression_archive_uri)

    def test_archive_pollination_input(self):
        params = {
            u'ag_classes': '67 68 71 72 73 74 75 76 78 79 80 81 82 83 84 85 88 90 91 92',
            u'do_valuation': True,
            u'farms_shapefile':
            u'data/pollination/samp_input/farms.shp',
            u'guilds_uri':
            u'data/pollination/samp_input/Guild.csv',
            u'half_saturation': 0.125,
            u'landuse_attributes_uri': u'data/pollination/samp_input/LU.csv',
            u'landuse_cur_uri': u'data/base_data/terrestrial/lulc_samp_cur/hdr.adf',
            u'landuse_fut_uri': u'data/base_data/terrestrial/lulc_samp_fut/hdr.adf',
            u'results_suffix': 'suff',
            u'wild_pollination_proportion': 1.0,
            u'workspace_dir': u'/home/jadoug06/workspace/Pollination_Mary',
        }

        archive_uri = os.path.join(TEST_OUT, 'pollination_input')
        data_storage.collect_parameters(params, archive_uri)

        archive_uri += '.tar.gz'
        regression_archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'pollination_input.tar.gz')
        self.assertArchive(archive_uri, regression_archive_uri)

    def test_extract_archive(self):
        workspace = raster_utils.temporary_folder()
        archive_uri = os.path.join(REGRESSION_ARCHIVES,
            'pollination_input.tar.gz')
        parameters = data_storage.extract_parameters_archive(workspace,
            archive_uri)

        self.maxDiff = None
        regression_params = {
            u'ag_classes': u'67 68 71 72 73 74 75 76 78 79 80 81 82 83 84 85 88 90 91 92',
            u'do_valuation': True,
            u'farms_shapefile': os.path.join(workspace, u'vector_LCN2UV'),
            u'guilds_uri': os.path.join(workspace, u'Guild.csv'),
            u'half_saturation': 0.125,
            u'landuse_attributes_uri': os.path.join(workspace, u'LU.csv'),
            u'landuse_cur_uri': os.path.join(workspace, u'raster_23KPVQ'),
            u'landuse_fut_uri': os.path.join(workspace, u'raster_N243QT'),
            u'results_suffix': u'suff',
            u'wild_pollination_proportion': 1.0,
        }

        self.assertEqual(parameters, regression_params)

        for key in ['farms_shapefile', 'guilds_uri', 'landuse_attributes_uri',
            'landuse_cur_uri', 'landuse_fut_uri']:
            self.assertEqual(True, os.path.exists(parameters[key]))
