"""This file will contain unittests for the biophysical component of the
pollination model."""

import unittest
import os
import shutil
import logging

import invest_natcap.pollination.pollination as pollination
import invest_natcap.pollination.pollination_core as pollination_core
import invest_natcap.testing as testing


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

TEST_DATA_DIR = 'invest-data/test/data/pollination/samp_input'
REGRESSION_FOLDER_BASE = 'invest-data/test/data/pollination/'
LOGGER = logging.getLogger('pollination_test')

WORKSPACE_DIR = 'invest-data/test/data/pollination/test_workspace'
GUILDS_URI = TEST_DATA_DIR + '/Guild.csv'

class UnifiedPollinationTest(testing.GISTest):
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
        try:
            shutil.rmtree(self.workspace_dir)
        except OSError:
            # Thrown when self.workspace_dir was not created.
            pass

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
            self.assertRastersEqual(test_file, reg_file)

    def test_farms_shapefile_already_exists(self):
        self.args['farms_shapefile'] = os.path.join(TEST_DATA_DIR, 'farms.shp')
        self.args['guilds_uri'] = os.path.join(TEST_DATA_DIR,
            'Guild_with_crops.csv')

        pollination.execute(self.args)

        regression_file = os.path.join(REGRESSION_FOLDER_BASE, 'biophysical_output',
            'farms_abundance_cur', 'farms.shp')
        test_file = os.path.join(self.workspace_dir, 'output',
            'farms_abundance_cur', 'farms.shp')
        self.assertVectorsEqual(regression_file,
            test_file)

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
        self.args['landuse_cur_uri'] = 'invest-data/test/data/base_data/terrestrial/lulc_samp_cur'
        pollination.execute(self.args)

    def test_ag_200m_smoke(self):
        self.args['ag_classes'] = str('67 68 71 72 73 74 75 76 78 79 80 81 82'
            + ' 83 84 85 88 90 91 92')
        self.args['landuse_cur_uri'] =\
            'invest-data/test/data/pollination/samp_input/landuse_cur_200m.tif'
        pollination.execute(self.args)

    def test_noag_200m_smoke(self):
        self.args['landuse_cur_uri'] =\
            'invest-data/test/data/pollination/samp_input/landuse_cur_200m.tif'
        pollination.execute(self.args)

    @unittest.skip('This takes too long.  Only run if you really mean it')
    def test_1m_smoke(self):
        self.args['workspace_dir'] = '/backup/manual-backup/pollination_test_workspace'
        self.args['landuse_cur_uri'] = '/backup/manual-backup/lulc_1m.tif'
        pollination.execute(self.args)


import invest_natcap.testing
class PollinationRegression(invest_natcap.testing.GISTest):
    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_pollination_ag_cur_noval_no_spp_weight.tar.gz",
        workspace_archive="data/pollination/output_pollination_ag_cur_noval_no_spp_weight.tar.gz")
    def test_pollination_ag_cur_noval_no_spp_weight(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_pollination_noag_cur_val.tar.gz",
        workspace_archive="data/pollination/output_pollination_noag_cur_val.tar.gz")
    def test_pollination_noag_cur_val(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_pollination_noag_cur_noval.tar.gz",
        workspace_archive="data/pollination/output_pollination_noag_cur_noval.tar.gz")
    def test_pollination_noag_cur_noval(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_noag_cur_only.tar.gz",
        workspace_archive="data/pollination/output_noag_cur_only.tar.gz")
    def test_noag_cur_only(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_noag_cur_fut_noval.tar.gz",
        workspace_archive="data/pollination/output_noag_cur_fut_noval.tar.gz")
    def test_noag_cur_fut_noval(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_noag_cur_fut.tar.gz",
        workspace_archive="data/pollination/output_noag_cur_fut.tar.gz")
    def test_noag_cur_fut(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_noag_cur_fut_farms.tar.gz",
        workspace_archive="data/pollination/output_noag_cur_fut_farms.tar.gz")
    def test_noag_cur_fut_farms(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_val.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_val.tar.gz")
    def test_ag_cur_val(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_only.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_only.tar.gz")
    def test_ag_cur_only(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_noval.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_noval.tar.gz")
    def test_ag_cur_noval(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_fut_noval.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_fut_noval.tar.gz")
    def test_ag_cur_fut_noval(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_fut.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_fut.tar.gz")
    def test_ag_cur_fut(self):
        invest_natcap.pollination.pollination.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="data/pollination/input_ag_cur_fut_farms.tar.gz",
        workspace_archive="data/pollination/output_ag_cur_fut_farms.tar.gz")
    def test_ag_cur_fut_farms(self):
        invest_natcap.pollination.pollination.execute(self.args)

