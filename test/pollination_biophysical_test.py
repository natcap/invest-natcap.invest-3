"""This file will contain unittests for the biophysical component of the
pollination model."""

import unittest
import os

import invest_test_core
import invest_natcap.pollination.pollination_biophysical as\
    pollination_biophysical
import invest_natcap.pollination.pollination_valuation as\
    pollination_valuation
import invest_natcap.pollination.pollination_core as pollination_core

TEST_DATA_DIR = 'data/pollination/samp_input'
REGRESSION_FOLDER_BASE = 'data/pollination/'

class PollinationTest(unittest.TestCase):
    def setUp(self):
        self.intermediate_rasters = {'workspace_subfolder': 'intermediate',
                                     'raster_uri_base': [],
                                     'uri_mid' : []}

        self.output_rasters = {'workspace_subfolder': 'output',
                               'raster_uri_base': [],
                               'uri_mid': []}

    def assert_pollination_rasters(self, test_path):
        for test_folder in [self.intermediate_rasters, self.output_rasters]:
            out_folder_name = os.path.join(self.args['workspace_dir'],
                test_folder['workspace_subfolder'])
            test_folder_name = os.path.join(test_path,
                test_folder['workspace_subfolder'])

            for uri_base in test_folder['raster_uri_base']:
                uri_base += '.tif'
                for uri_mid in test_folder['uri_mid']:
                    test_raster_uri = pollination_core.build_uri(out_folder_name,
                        uri_base, [uri_mid, 'cur'])
                    reg_raster_uri = pollination_core.build_uri(out_folder_name,
                        uri_base, [uri_mid, 'cur'])

                    invest_test_core.assertTwoDatasetEqualURI(self,
                        test_raster_uri, reg_raster_uri)


class PollinationBiophysicalTest(PollinationTest):
    def setUp(self):
        """Set up arguments dictionary and other inputs."""
        self.args = {'workspace_dir': 'data/pollination/test_workspace',
                     'landuse_cur_uri': TEST_DATA_DIR + '/landuse_cur_200m.tif',
                     'landuse_attributes_uri': TEST_DATA_DIR + '/LU.dbf',
                     'guilds_uri': TEST_DATA_DIR + '/Guild.dbf'}

        self.valuation_args = {'workspace_dir': self.args['workspace_dir'],
                               'guilds_uri': self.args['guilds_uri'],
                               'half_saturation': 0.125,
                               'wild_pollination_proportion': 1}

        self.intermediate_rasters = {'workspace_subfolder': 'intermediate',
                                     'raster_uri_base': ['frm', 'hf',
                                                         'hn', 'sup'],
                                     'uri_mid' : ['Apis', 'Bombus']}

        self.output_rasters = {'workspace_subfolder': 'output',
                               'raster_uri_base': ['frm_avg', 'sup_tot'],
                               'uri_mid': ['']}

    def test_regression(self):
        """Regression test for pollination_biophysical."""
        pollination_biophysical.execute(self.args)
        self.assert_pollination_rasters(os.path.join('biophysical_output',
            REGRESSION_FOLDER_BASE, 'no_ag_classes'))

    def test_ag_classes(self):
        """Regression test for pollination_biophysical.  Includes ag classes."""
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        pollination_biophysical.execute(self.args)
        self.assert_pollination_rasters(os.path.join('biophysical_output',
            REGRESSION_FOLDER_BASE, 'with_ag_classes'))
