"""This file will contain unittests for the biophysical component of the
pollination model."""

import unittest

import invest_natcap.pollination.pollination_biophysical as\
    pollination_biophysical
import invest_natcap.pollination.pollination_valuation as\
    pollination_valuation

TEST_DATA_DIR = 'data/pollination/samp_input'


class PollinationBiophysicalTest(unittest.TestCase):
    def setUp(self):
        """Set up arguments dictionary and other inputs."""
        self.args = {'workspace_dir': 'data/pollination/test_workspace',
                     'landuse_uri': 'data/base_data/terrestrial/lulc_samp_cur',
                     'landuse_attributes_uri': TEST_DATA_DIR + '/LU.dbf',
                     'guilds_uri': TEST_DATA_DIR + '/Guild.dbf'}

        self.valuation_args = {'workspace_dir': self.args['workspace_dir'],
                               'guilds_uri': self.args['guilds_uri'],
                               'half_saturation': 0.125,
                               'wild_pollination_proportion': 1}

#    def test_smoke(self):
#        """Smoke test for pollination_biophysical."""
#        pollination_biophysical.execute(self.args)

    def test_ag_classes(self):
        """Smoke test for pollination_biophysical.  Includes ag classes."""
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        pollination_biophysical.execute(self.args)
        pollination_valuation.execute(self.valuation_args)
