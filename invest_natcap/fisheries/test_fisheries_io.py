import unittest
import os
import pprint

from numpy import testing
import numpy as np

import fisheries
import fisheries_io

from fisheries_io import MissingParameter

data_directory = '../../test/invest-data/test/data/fisheries'
pp = pprint.PrettyPrinter(indent=4)


All_Parameters = ['Classes', 'Duration', 'Exploitationfraction', 'Fecundity',
                  'Larvaldispersal', 'Maturity', 'Regions', 'Survnaturalfrac',
                  'Weight', 'Vulnfishing']
Necessary_Params = ['Classes', 'Exploitationfraction', 'Maturity', 'Regions',
                    'Survnaturalfrac', 'Vulnfishing']


class TestPopulationParamsIO(unittest.TestCase):
    def test_parse_popu_params_sn(self):
        uri = os.path.join(data_directory, 'CSVs/TestCSV_SN_Syntax.csv')
        sexsp = 1
        pop_dict = fisheries_io._parse_population_csv(uri, sexsp)
        # Check that keys are correct
        Matching_Keys = [i for i in pop_dict.keys() if i in All_Parameters]
        self.assertEqual(len(Matching_Keys), len(All_Parameters))
        # Check that sexsp handled correctly
        self.assertEqual(len(pop_dict['Survnaturalfrac']), sexsp)
        # Check that Class attribute lengths match
        self.assertEqual(
            len(pop_dict['Vulnfishing']), len(pop_dict['Maturity']))
        # Print Dictionary if debugging
        #pp.pprint(pop_dict)

    def test_parse_popu_params_ss(self):
        uri = os.path.join(data_directory, 'CSVs/TestCSV_SS_Syntax.csv')
        sexsp = 2
        pop_dict = fisheries_io._parse_population_csv(uri, sexsp)
        # Check that keys are correct
        Matching_Params = [i for i in pop_dict.keys() if i in All_Parameters]
        self.assertEqual(len(Matching_Params), len(All_Parameters))
        # Check that sexsp handled correctly
        self.assertEqual(len(pop_dict['Survnaturalfrac']), sexsp)
        # Check that Class attribute lengths match
        self.assertEqual(
            len(pop_dict['Vulnfishing']), len(pop_dict['Maturity']))
        # Print Dictionary if debugging
        #pp.pprint(pop_dict)

    def test_verify_popu_params(self):
        # Check that throws error when necessary information does not exist

        # Test with not all necessary params
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail1.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        with self.assertRaises(MissingParameter):
            fisheries_io._verify_population_csv(args)

        # Test Stage-based without Duration vector
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail2.csv')
        args['population_csv_uri'] = population_csv_uri
        args['population_type'] = 'Stage-Based'
        with self.assertRaises(MissingParameter):
            fisheries_io._verify_population_csv(args)

        # Test B-H / Weight without Weight vector
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail3.csv')
        args['population_csv_uri'] = population_csv_uri
        args['recruitment_type'] = 'Beverton-Holt'
        args['spawn_units'] = 'Weight'
        with self.assertRaises(MissingParameter):
            fisheries_io._verify_population_csv(args)

        # Test Fecundity without Fecundity vector
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail3.csv')
        args['population_csv_uri'] = population_csv_uri
        args['recruitment_type'] = 'Fecundity'
        args['harvest_units'] = 'Weight'
        with self.assertRaises(MissingParameter):
            fisheries_io._verify_population_csv(args)

        '''
        # Check that throws error when incorrect information exists
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Semantics_fail1.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))

        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Semantics_fail2.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))

        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Semantics_fail3.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))
        '''


class TestMigrationIO(unittest.TestCase):
    def test_parse_migration(self):
        uri = os.path.join(data_directory, 'Migration/')
        args = {
            'migr_cont': True,
            'migration_dir': uri
        }
        class_list = ['larva', 'adult']
        mig_dict = fisheries_io._parse_migration_tables(args, class_list)
        #pp.pprint(mig_dict)
        self.assertIsInstance(mig_dict['adult'], np.matrix)
        self.assertEqual(
            mig_dict['adult'].shape[0], mig_dict['adult'].shape[1])

    def test_verify_migration(self):
        uri = os.path.join(data_directory, 'Migration/')
        args = {
            "migration_dir": uri,
            "migr_cont": True,
            }
        class_list = ['larva', 'other', 'other2', 'adult']
        region_list = ['Region 1', 'Region 2', '...', 'Region N']
        mig_dict = fisheries_io._verify_migration_tables(
            args, class_list, region_list)
        test_matrix_dict = fisheries_io._parse_migration_tables(args, ['larva'])
        #pp.pprint(test_matrix_dict)
        #pp.pprint(mig_dict)
        testing.assert_array_equal(
            mig_dict['Migration'][0], test_matrix_dict['larva'])


class TestSingleParamsIO(unittest.TestCase):
    def test_verify_single_params(self):
        #home_dir = os.path.expanduser("~")
        workspace_dir = "/test_workspace"
        args = {
            'workspace_dir': workspace_dir,
            'aoi_uri': None,
            'population_type': None,
            'sexsp': 1,
            'total_init_recruits': -1.0,
            'total_timesteps': -1,
            'recruitment_type': 'Ricker',
            'spawn_units': 'Individuals',
            'alpha': None,
            'beta': None,
            'total_recur_recruits': None,
            'migr_cont': True,
            'harvest_units': None,
            'frac_post_process': None,
            'unit_price': None,
            'harv_cont': True,
            }

        # Check that path exists and user has read/write permissions along path
        with self.assertRaises(OSError):
            fisheries_io._verify_single_params(args)
        args['workspace_dir'] = os.path.join(os.getcwd(), 'test')

        # Check timesteps positive number
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['total_timesteps'] = 100

        # Check total_init_recruits for non-negative float
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['total_init_recruits'] = 1.2

        # Check recruitment type's corresponding parameters exist
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['alpha'] = -1.0
        args['beta'] = -1.0
        args['total_recur_recruits'] = -1.0

        # If BH or Ricker: Check alpha positive float
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['alpha'] = 1.0

        # Check positive beta positive float
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['beta'] = 1.0

        # Check total_recur_recruits is non-negative float
        args['recruitment_type'] = 'Fixed'
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['total_recur_recruits'] = 100.0

        # If Harvest: Check frac_post_process float between [0,1]
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['frac_post_process'] = 0.2

        # If Harvest: Check unit_price non-negative float
        with self.assertRaises(ValueError):
            fisheries_io._verify_single_params(args)
        args['unit_price'] = 20.2

        # Check file extension? (maybe try / except would be better)
        # Check shapefile subregions match regions in population parameters file
        args['aoi_uri'] = None

        # Clean up filesystem
        os.rmdir(args['workspace_dir'])


class TestFetchVerifyArgs(unittest.TestCase):
    def test_fetch_verify(self):
        csv_uri = os.path.join(data_directory, 'CSVs/TestCSV_SN_Syntax.csv')
        mig_uri = os.path.join(data_directory, 'Migration/')
        workspace_dir = os.path.join(os.getcwd(), 'test')
        args = {
            'population_csv_uri': csv_uri,
            'migr_cont': True,
            'migration_dir': mig_uri,
            'workspace_dir': workspace_dir,
            'aoi_uri': None,
            'population_type': "Stage-Based",
            'sexsp': 1,
            'total_init_recruits': 1.2,
            'total_timesteps': 100,
            'recruitment_type': 'Ricker',
            'spawn_units': 'Individuals',
            'alpha': 1.0,
            'beta': 1.2,
            'total_recur_recruits': 100.0,
            'migr_cont': True,
            'harvest_units': "Weight",
            'frac_post_process': 0.2,
            'unit_price': 20.2,
            'harv_cont': True,
        }
        vars_dict = fisheries_io.fetch_verify_args(args)
        #pp.pprint(vars_dict)
        #with self.assertRaises():
        #    fisheries_io.fetch_verify_args(args)


class TestInitializeVars(unittest.TestCase):
    def test_calc_survtotalfrac(self):
        # Test very simple
        vars_dict = {
            'Survnaturalfrac': np.array([[
                [1.0, 1.0], [1.0, 1.0]],
                [[1.0, 1.0], [1.0, 1.0]]]),
            'Exploitationfraction': np.array([1.0,  1.0]),
            'Vulnfishing': np.array([[1.0,  1.0], [1.0,  1.0]]),
        }

        ans = fisheries_io._calc_survtotalfrac(vars_dict)
        testing.assert_array_equal(ans, np.zeros([2, 2, 2]))

        # Test simple
        vars_dict = {
            'Survnaturalfrac': np.array([[
                [0.75, 0.25], [0.25, 0.75]],
                [[0.5, 0.75], [0.75, 0.5]]]),
            'Exploitationfraction': np.array([0.5, 0.25]),
            'Vulnfishing': np.array([[0.1, 0.2], [0.3, 0.4]]),
        }
        check = np.array([[[0.7125, 0.24375], [0.225, 0.7125]], [[0.425, 0.69375], [0.6, 0.45]]])

        ans = fisheries_io._calc_survtotalfrac(vars_dict)
        testing.assert_array_almost_equal(ans, check)

        # Test larger arrays
        vars_dict = {
            'Survnaturalfrac': np.ones([2, 3, 4]),
            'Exploitationfraction': np.ones((1, 4)),
            'Vulnfishing': np.ones((2, 3)),
        }

        ans = fisheries_io._calc_survtotalfrac(vars_dict)
        print "Ans"
        pp.pprint(ans)
        testing.assert_array_almost_equal(ans, np.zeros([2, 3, 4]))

    def test_p_g_survtotalfrac(self):
        # Test simple
        vars_dict = {
            'Survtotalfrac': np.array([[
                [1.0, 2.0], [3.0, 4.0]],
                [[5.0, 6.0], [7.0, 8.0]]]),
            'Duration': np.array([[1, 2], [3, 4]]),
        }
        G_check = np.array([[[1.0, 2.0], [9.0, 16.0]],[[125.0, 216.0], [2401.0, 4096.0]]])

        G, P = fisheries_io._calc_p_g_survtotalfrac(vars_dict)
        testing.assert_array_equal(G, G_check)

        pass

    def test_initialize_vars(self):
        pass
    pass

if __name__ == '__main__':
    unittest.main()
