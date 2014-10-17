import unittest
import os

from numpy import testing
import numpy as np

import fisheries
import fisheries_io

data_directory = '../../test/invest-data/test/data/fisheries'


class TestPopulationParamsIO(unittest.TestCase):
    def test_parse_popu_params_sn(self):
        uri = os.path.join(data_directory, 'CSVs/TestCSV_SN_Syntax.csv')
        sexsp = 1
        pop_dict = fisheries_io._parse_population_csv(uri, sexsp)
        self.assertEqual(len(pop_dict['SurvNaturalFrac']), sexsp)
        self.assertIn('VulnFishing', pop_dict)
        self.assertEqual(
            len(pop_dict['VulnFishing']), len(pop_dict['Maturity']))
        print "classes:", pop_dict['classes']
        print "regions:", pop_dict['regions']

    def test_parse_popu_params_ss(self):
        uri = os.path.join(data_directory, 'CSVs/TestCSV_SS_Syntax.csv')
        sexsp = 2
        pop_dict = fisheries_io._parse_population_csv(uri, sexsp)
        self.assertEqual(len(pop_dict['SurvNaturalFrac']), sexsp)
        self.assertIn('VulnFishing', pop_dict)
        self.assertEqual(
            len(pop_dict['VulnFishing']), len(pop_dict['Maturity']))
        print "classes:", pop_dict['classes']
        print "regions:", pop_dict['regions']

    def test_verify_popu_params(self):
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
