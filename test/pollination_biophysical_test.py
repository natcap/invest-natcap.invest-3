"""This file will contain unittests for the biophysical component of the
pollination model."""

import unittest
import os
import shutil
import logging

import invest_test_core
import invest_natcap.pollination.pollination_biophysical as\
    pollination_biophysical
import invest_natcap.pollination.pollination_valuation as\
    pollination_valuation
import invest_natcap.pollination.pollination_core as pollination_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

TEST_DATA_DIR = 'data/pollination/samp_input'
REGRESSION_FOLDER_BASE = 'data/pollination/'
LOGGER = logging.getLogger('pollination_test')

class PollinationTest(unittest.TestCase):
    """This class contains information specific to the Pollination models, but
        shared between both the biophysical and Valuation components."""

    def setUp(self):
        """Reimplemented from unittest.TestCase, this has information that is
            used by both the biophysical and valuation components. """
        self.workspace_dir = 'data/pollination/test_workspace'
        self.guilds_uri = TEST_DATA_DIR + '/Guild.csv'

        # The structure of self.intermediate_rasters and self.output_rasters
        # should be maintained across subclasses, although their contents may be
        # altered according to the needs of the subclass.  These two
        # dictionaries are used by self.assert_pollination_rasters().
        self.intermediate_rasters = {'workspace_subfolder': 'intermediate',
                                     'raster_uri_base': [],
                                     'uri_mid' : []}

        self.output_rasters = {'workspace_subfolder': 'output',
                               'raster_uri_base': [],
                               'uri_mid': []}

#    def tearDown(self):
#        shutil.rmtree(self.workspace_dir)

    def assert_pollination_rasters(self, test_path):
        """Assert that all rasters produced by this component of the pollination
            model match their corresponding regression rasters.  This function
            uses self.intermediate_rasters and self.output_rasters dictionaries
            to assemble the correct URIs.

            test_path - a python string representing the path to the folder
                containing regression rasters.  Note that this folder's
                structure should match the structure of the pollination model.

            returns nothing"""

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
                    reg_raster_uri = pollination_core.build_uri(test_folder_name,
                        uri_base, [uri_mid, 'cur'])

                    LOGGER.debug('Asserting rasters.  Test=%s, Reg=%s',
                                 test_raster_uri, reg_raster_uri)
                    invest_test_core.assertTwoDatasetEqualURI(self,
                        test_raster_uri, reg_raster_uri)


class PollinationBiophysicalTest(PollinationTest):
    def setUp(self):
        """Set up arguments dictionary and other inputs."""
        PollinationTest.setUp(self)
        self.args = {'workspace_dir': self.workspace_dir,
                     'landuse_cur_uri': TEST_DATA_DIR + '/landuse_cur_200m.tif',
                     'landuse_attributes_uri': TEST_DATA_DIR + '/LU.csv',
                     'guilds_uri': self.guilds_uri}

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
        self.assert_pollination_rasters(os.path.join(REGRESSION_FOLDER_BASE,
            'biophysical_output','no_ag_classes'))

    def test_ag_classes(self):
        """Regression test for pollination_biophysical.  Includes ag classes."""
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        pollination_biophysical.execute(self.args)
        self.assert_pollination_rasters(os.path.join(REGRESSION_FOLDER_BASE,
            'biophysical_output', 'with_ag_classes'))


class PollinationValuationTest(PollinationTest):
    def setUp(self):
        PollinationTest.setUp(self)
        self.args = {'workspace_dir': self.workspace_dir,
                     'guilds_uri': self.guilds_uri,
                     'half_saturation': 0.125,
                     'wild_pollination_proportion': 1}

        self.intermediate_rasters = {'workspace_subfolder': 'intermediate',
                                     'raster_uri_base': ['frm_val_sum',
                                        'frm_val_Apis', 'frm_val_Bombus'],
                                     'uri_mid' : ['']}

        self.output_rasters = {'workspace_subfolder': 'output',
                               'raster_uri_base': ['sup_val_sum',
                                    'sup_val_Apis', 'sup_val_Bombus'],
                               'uri_mid': ['']}

        # The valuation component needs to be started with the appropriate
        # datasets in the workspace, so we need to delete the existing workspace
        # if it exists in the filesystem, we should remove it and copy over a
        # complete set of regression rasters for use by the valuation
        # component.
        self.biophysical_sample_dir = os.path.join(REGRESSION_FOLDER_BASE,
            'biophysical_output', 'with_ag_classes')
        try:
            shutil.rmtree(self.workspace_dir)
        except OSError:
            # OSError is thrown when self.workspace_dir doesn't exist in the
            # filesystem.  In this case, we don't need to do anything.
            pass
        shutil.copytree(self.biophysical_sample_dir, self.workspace_dir)

    def tearDown(self):
        """This function is called at the end of each test.  For
            pollination_valuation, this function removes the workspace directory
            from the filesystem."""
        shutil.rmtree(self.workspace_dir)

    def test_regression(self):
        """Regression test for pollination_valuation."""
        pollination_valuation.execute(self.args)
        self.assert_pollination_rasters(os.path.join(REGRESSION_FOLDER_BASE,
            'valuation_output', 'with_ag_classes'))

class UnifiedPollinationTest(PollinationTest):
    def setUp(self):
        PollinationTest.setUp(self)
        self.args = {
            'workspace_dir': self.workspace_dir,
            'landuse_cur_uri': os.path.join(TEST_DATA_DIR, 'landuse_cur_200m.tif'),
            'landuse_attributes_uri': os.path.join(TEST_DATA_DIR, 'LU.csv'),
            'guilds_uri': self.guilds_uri,
            'half_saturation': 0.125,
            'wild_pollination_proportion': 1
        }

    def test_regression(self):
        pollination.execute(self.args)

        intermediate_files = ['%s.tif' % '_'.join(filename) for filename in
            [
                [prefix, species, scenario]
                for prefix in ['frm', 'hf', 'hn','sup']
                for species in ['Apis', 'Bombus']
                for scenario in ['cur']
            ]
        ]

        # Verify all intermediate files from biophysical
        for filename in intermediate_files:
            test_file = os.path.join(self.workspace_dir, 'intermediate', filename)
            reg_file = os.path.join(TEST_DATA_DIR, 'biophysical_output', 'no_ag_classes',
                'intermediate', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        # Build up a list of all output files
        output_files = ['%s_cur.tif' % '_'.join(filename) for filename in
            ['sup_val_sum', 'sup_val_Apis', 'sup_val_Bombus']]

        # Verify all output files from biophysical
        for filename in output_files:
            test_file = os.path.join(self.workspace_dir, 'output', filename)
            reg_file = os.path.join(TEST_DATA_DIR, 'biophysical_output', 'no_ag_classes',
                'output', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)


class PollinationSmokeTest(PollinationBiophysicalTest):
    """To only run this test class at the command line, do this:
       $ nosetests -vs pollination_biophysical_test.py:PollinationSmokeTest.test_ag_30m_smoke

       To run other tests, run:
       $ nosetests -vs pollination_biophysical_test.py:Pollination{Biophysical,Valuation}Test
       """
    def setUp(self):
        PollinationBiophysicalTest.setUp(self)
        self.value_args = {'workspace_dir': self.workspace_dir,
                           'guilds_uri': self.guilds_uri,
                           'half_saturation': 0.125,
                           'wild_pollination_proportion': 1}

    def test_ag_30m_smoke(self):
        """Smoke test for pollination_biophysical at 30m.  Includes ag classes.
        """
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        self.args['landuse_cur_uri'] = 'data/base_data/terrestrial/lulc_samp_cur'
        pollination_biophysical.execute(self.args)
        pollination_valuation.execute(self.value_args)

    def test_ag_200m_smoke(self):
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        self.args['landuse_cur_uri'] =\
            'data/pollination/samp_input/landuse_cur_200m.tif'
        pollination_biophysical.execute(self.args)
        pollination_valuation.execute(self.value_args)


    def test_noag_200m_smoke(self):
        self.args['landuse_cur_uri'] =\
            'data/pollination/samp_input/landuse_cur_200m.tif'
        pollination_biophysical.execute(self.args)
        pollination_valuation.execute(self.value_args)

    @unittest.skip('This takes too long.  Only run if you really mean it')
    def test_1m_smoke(self):
        self.args['workspace_dir'] = '/backup/manual-backup/pollination_test_workspace'
        self.args['landuse_cur_uri'] = '/backup/manual-backup/lulc_1m.tif'
        pollination_biophysical.execute(self.args)
        pollination_valuation.execute(self.value_args)
