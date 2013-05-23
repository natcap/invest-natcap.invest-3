import unittest
import os

import invest_natcap.testing as testing
from invest_natcap.testing import data_storage

POLLINATION_DATA = os.path.join('data', 'pollination', 'samp_input')
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
