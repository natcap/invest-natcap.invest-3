import unittest
import os

from numpy import testing

import fisheries
import fisheries_io

data_directory = '../../test/invest-data/test/data/fisheries'


class TestMigrationIO(unittest.TestCase):
    def test_parse_migration(self):
        uri = os.path.join(data_directory, 'Migration/')
        mig_dict = fisheries_io._parse_migration_tables(uri)
        print mig_dict

    def test_verify_migration(self):
        pass


class TestPopulationParamsIO(unittest.TestCase):
    def test_parse_popu_params_sn(self):
        uri = os.path.join(data_directory, 'CSV/sex_neutral.csv')
        sexsp = 1
        pop_dict = fisheries_io._parse_population_csv(uri,sexsp)
        print pop_dict

    def test_parse_popu_params_ss(self):
        uri = os.path.join(data_directory, 'CSV/sex_specific.csv')
        sexsp = 2
        pop_dict = fisheries_io._parse_population_csv(uri,sexsp)
        print pop_dict

    def test_verify_popu_params(self):
        pass


if __name__ == '__main__':
    unittest.main()
