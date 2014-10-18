import unittest
import os
import pprint

from numpy import testing
import numpy as np

import fisheries
import fisheries_io

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
        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail1.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))

        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail2.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))

        population_csv_uri = os.path.join(data_directory, 'CSVs/Fail/TestCSV_SN_Syntax_fail3.csv')
        args = {'population_csv_uri': population_csv_uri, 'sexsp': 1}
        self.assertRaises(
            MissingParameter, fisheries_io._verify_population_csv(args))

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

        pass


class TestMigrationIO(unittest.TestCase):
    def test_parse_migration(self):
        uri = os.path.join(data_directory, 'Migration/')
        mig_dict = fisheries_io._parse_migration_tables(uri)
        self.assertIsInstance(mig_dict['adult'], np.matrix)
        self.assertEqual(
            mig_dict['adult'].shape[0], mig_dict['adult'].shape[1])

    def test_verify_migration(self):
        pass


if __name__ == '__main__':
    unittest.main()
