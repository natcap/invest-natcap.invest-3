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
import invest_natcap.pollination.pollination as pollination
import invest_natcap.pollination.pollination_core as pollination_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

TEST_DATA_DIR = 'data/pollination/samp_input'
REGRESSION_FOLDER_BASE = 'data/pollination/'
LOGGER = logging.getLogger('pollination_test')

WORKSPACE_DIR = 'data/pollination/test_workspace'
GUILDS_URI = TEST_DATA_DIR + '/Guild.csv'

class UnifiedPollinationTest(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = WORKSPACE_DIR
        self.guilds_uri = GUILDS_URI

        self.args = {
            'workspace_dir': self.workspace_dir,
            'landuse_cur_uri': os.path.join(TEST_DATA_DIR, 'landuse_cur_200m.tif'),
            'landuse_attributes_uri': os.path.join(TEST_DATA_DIR, 'LU.csv'),
            'do_valuation': False,
            'guilds_uri': self.guilds_uri,
            'half_saturation': 0.125,
            'wild_pollination_proportion': 1,
            'do_valuation': False
        }

    def tearDown(self):
        """This function is called at the end of each test.  For
            pollination_valuation, this function removes the workspace directory
            from the filesystem."""
        shutil.rmtree(self.workspace_dir)

    def test_regression_biophysical(self):
        pollination.execute(self.args)

        intermediate_files = ['%s.tif' % '_'.join(filename) for filename in [
            [prefix, species, scenario]
            for prefix in ['frm', 'hf', 'hn','sup']
            for species in ['Apis', 'Bombus']
            for scenario in ['cur']]]

        # Verify all intermediate files from biophysical
        LOGGER.debug('Checking intermediate files from biophysical')
        for filename in intermediate_files:
            test_file = os.path.join(self.workspace_dir, 'intermediate', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'no_ag_classes', 'intermediate', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        # Build up a list of all output files
        output_files = ['%s_cur.tif' % (filename) for filename in
            ['frm_avg', 'sup_tot']]

        # Verify all output files from biophysical
        LOGGER.debug('Checking output files from biophysical')
        for filename in output_files:
            test_file = os.path.join(self.workspace_dir, 'output', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'no_ag_classes', 'output', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

    def test_regression_biophysical_ag_classes(self):
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            ' 83 84 85 88 90 91 92')
        pollination.execute(self.args)

        intermediate_files = ['%s.tif' % '_'.join(filename) for filename in [
            [prefix, species, scenario]
            for prefix in ['frm', 'hf', 'hn','sup']
            for species in ['Apis', 'Bombus']
            for scenario in ['cur']]]

        # Verify all intermediate files from biophysical
        LOGGER.debug('Checking intermediate files from biophysical')
        for filename in intermediate_files:
            test_file = os.path.join(self.workspace_dir, 'intermediate', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'with_ag_classes', 'intermediate', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        # Build up a list of all output files
        output_files = ['%s_cur.tif' % (filename) for filename in
            ['frm_avg', 'sup_tot']]

        # Verify all output files from biophysical
        LOGGER.debug('Checking output files from biophysical')
        for filename in output_files:
            test_file = os.path.join(self.workspace_dir, 'output', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'with_ag_classes', 'output', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

    def test_regression_valuation(self):
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            ' 83 84 85 88 90 91 92')
        self.args['do_valuation'] = True
        pollination.execute(self.args)

        intermediate_files = ['%s.tif' % '_'.join(filename) for filename in [
            [prefix, species, scenario]
            for prefix in ['frm', 'hf', 'hn','sup']
            for species in ['Apis', 'Bombus']
            for scenario in ['cur']]]

        # Verify all intermediate files from biophysical
        LOGGER.debug('Checking intermediate files from biophysical')
        for filename in intermediate_files:
            test_file = os.path.join(self.workspace_dir, 'intermediate', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'with_ag_classes', 'intermediate', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        # Build up a list of all output files
        output_files = ['%s_cur.tif' % (filename) for filename in
            ['frm_avg', 'sup_tot']]

        # Verify all output files from biophysical
        LOGGER.debug('Checking output files from valuation')
        for filename in output_files:
            test_file = os.path.join(self.workspace_dir, 'output', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'with_ag_classes', 'output', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        val_inter_files = ['frm_val_%s_cur.tif' % part for part in
            ['Apis', 'Bombus', 'sum']]
        val_inter_files += ['sup_val_Apis_cur.tif', 'sup_val_Bombus_cur.tif']
        for filename in val_inter_files:
            test_file = os.path.join(self.workspace_dir, 'intermediate', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'valuation_output', 'with_ag_classes', 'intermediate', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

        # Build up a list of all output files
        val_output_files = ['sup_val_%s_cur.tif' % (filename) for filename in
            ['sum']]

        # Verify all output files from biophysical
        LOGGER.debug('Checking output files from valuation')
        for filename in val_output_files:
            test_file = os.path.join(self.workspace_dir, 'output', filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'valuation_output', 'with_ag_classes', 'output', filename)
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

    def test_one_species(self):
        # This test exists for the sake of issue 1536.
        # When Running a user's data, I encountered what appeared to be a bug in
        # InVEST 2.4.4, which would cause a raster to not have any values set to
        # it if there is only one species.
        #
        # In this test case, I have a test guilds file with only the Apis
        # species in it.  All I have to do, then, is check that frm_avg_cur.tif
        # and frm_Apis_cur.tif are equal to the regression file
        # frm_Apis_cur.tif.
        #
        # This test assumes that other bugs are caught by the other regression
        # tests.

        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            ' 83 84 85 88 90 91 92')
        self.args['guilds_uri'] = os.path.join(TEST_DATA_DIR,
            'apis_only_guild.csv')
        pollination.execute(self.args)

        files_to_check = ['output/frm_avg_cur.tif',
                          'intermediate/frm_Apis_cur.tif']

        for filename in files_to_check:
            test_file = os.path.join(self.workspace_dir, filename)
            reg_file = os.path.join(REGRESSION_FOLDER_BASE,
                'biophysical_output', 'with_ag_classes', 'intermediate',
                'frm_Apis_cur.tif')
            invest_test_core.assertTwoDatasetEqualURI(self, test_file, reg_file)

    def test_farms_shapefile(self):
        self.args['farms_shapefile'] = os.path.join(TEST_DATA_DIR, 'farms.shp')
        self.args['guilds_uri'] = os.path.join(TEST_DATA_DIR,
            'Guild_with_crops.csv')
        pollination.execute(self.args)


class PollinationSmokeTest(unittest.TestCase):
    """To only run this test class at the command line, do this:
       $ nosetests -vs pollination_biophysical_test.py:PollinationSmokeTest.test_ag_30m_smoke

       To run other tests, run:
       $ nosetests -vs pollination_biophysical_test.py:Pollination{Biophysical,Valuation}Test
       """
    def setUp(self):
        self.workspace_dir = WORKSPACE_DIR
        self.guilds_uri = GUILDS_URI

        self.args = {
            'workspace_dir': self.workspace_dir,
            'landuse_cur_uri': os.path.join(TEST_DATA_DIR, 'landuse_cur_200m.tif'),
            'landuse_attributes_uri': os.path.join(TEST_DATA_DIR, 'LU.csv'),
            'do_valuation': False,
            'guilds_uri': self.guilds_uri,
            'half_saturation': 0.125,
            'wild_pollination_proportion': 1,
            'do_valuation': False
        }

    def tearDown(self):
        """This function is called at the end of each test.  For
            pollination_valuation, this function removes the workspace directory
            from the filesystem."""
        shutil.rmtree(self.workspace_dir)

    def test_ag_30m_smoke(self):
        """Smoke test for pollination_biophysical at 30m.  Includes ag classes.
        """
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        self.args['landuse_cur_uri'] = 'data/base_data/terrestrial/lulc_samp_cur'
        pollination.execute(self.args)

    def test_ag_200m_smoke(self):
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        self.args['landuse_cur_uri'] =\
            'data/pollination/samp_input/landuse_cur_200m.tif'
        pollination.execute(self.args)

    def test_noag_200m_smoke(self):
        self.args['landuse_cur_uri'] =\
            'data/pollination/samp_input/landuse_cur_200m.tif'
        pollination.execute(self.args)

    @unittest.skip('This takes too long.  Only run if you really mean it')
    def test_1m_smoke(self):
        self.args['workspace_dir'] = '/backup/manual-backup/pollination_test_workspace'
        self.args['landuse_cur_uri'] = '/backup/manual-backup/lulc_1m.tif'
        pollination.execute(self.args)
