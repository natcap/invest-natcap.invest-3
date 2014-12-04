import unittest
import os
import pprint

from numpy import testing
import numpy as np
# from nose.plugins.skip import SkipTest

import fisheries

workspace_dir = '../../test/invest-data/Fisheries'
input_dir = '../../test/invest-data/Fisheries/Input'
pp = pprint.PrettyPrinter(indent=4)


class TestBlueCrab(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': workspace_dir,
            'aoi_uri': os.path.join(input_dir, 'Shapefile_Galveston/Galveston_Subregion.shp'),
            'total_timesteps': 100,
            'population_type': 'Age-Based',
            'sexsp': 'No',
            'harvest_units': 'Individuals',
            'do_batch': False,
            'population_csv_uri': os.path.join(input_dir, 'Inputs_BlueCrab/population_params.csv'),
            'spawn_units': 'Individuals',
            'total_init_recruits': 200000.0,
            'recruitment_type': 'Ricker',
            'alpha': 6050000.0,
            'beta': 0.0000000414,
            'total_recur_recruits': 0,
            'migr_cont': False,
            'migration_dir': '',
            'val_cont': False,
            'frac_post_process': 0.0,
            'unit_price': 0.0,
        }

    def test_run(self):
        guess = fisheries.execute(self.args, create_outputs=False)
        # pp.pprint(guess[0]['N_tasx'])

        # check harvest: 24,798,419
        harvest_guess = guess[0]['H_tx'][self.args['total_timesteps'] - 1].sum()
        testing.assert_approx_equal(harvest_guess, 24798419.0, significant=3)
        
        # check spawners: 42,644,460
        spawners_check = 42644460.0
        spawners_guess = guess[0]['Spawners_t'][self.args['total_timesteps'] - 1]
        testing.assert_approx_equal(spawners_guess, spawners_check, significant=4)


class TestDungenessCrab(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': workspace_dir,
            'aoi_uri': os.path.join(input_dir, 'Shapefile_HoodCanal/DC_HoodCanal_Subregions.shp'),
            'total_timesteps': 100,
            'population_type': 'Age-Based',
            'sexsp': 'Yes',
            'harvest_units': 'Individuals',
            'do_batch': False,
            'population_csv_uri': os.path.join(input_dir, 'Inputs_DungenessCrab/population_params.csv'),
            'spawn_units': 'Individuals',
            'total_init_recruits': 2249339326901,
            'recruitment_type': 'Ricker',
            'alpha': 2000000,
            'beta': 0.000000309,
            'total_recur_recruits': 0,
            'migr_cont': False,
            'migration_dir': '',
            'val_cont': False,
            'frac_post_process': 0.0,
            'unit_price': 0.0,
        }
        self.check = {

        }
    
    def test_run(self):
        guess = fisheries.execute(self.args, create_outputs=False)
        # pp.pprint(guess)

        # check harvest: 526,987
        harvest_check = 526987.0
        harvest_guess = guess[0]['H_tx'][self.args['total_timesteps'] - 1].sum()
        testing.assert_approx_equal(harvest_guess, harvest_check, significant=2)

        # check spawners: 4,051,538
        spawners_check = 4051538.0
        spawners_guess = guess[0]['Spawners_t'][self.args['total_timesteps'] - 1]
        testing.assert_approx_equal(spawners_guess, spawners_check, significant=3)


class TestLobster(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': workspace_dir,
            'aoi_uri': os.path.join(input_dir, 'Shapefile_Belize/Lob_Belize_Subregions.shp'),
            'total_timesteps': 100,
            'population_type': 'Age-Based',
            'sexsp': 'No',
            'harvest_units': 'Weight',
            'do_batch': False,
            'population_csv_uri': os.path.join(input_dir, 'Inputs_Lobster/population_params.csv'),
            'spawn_units': 'Weight',
            'total_init_recruits': 4686959.0,
            'recruitment_type': 'Beverton-Holt',
            'alpha': 5770000.0,
            'beta': 2885000.0,
            'total_recur_recruits': 0,
            'migr_cont': True,
            'migration_dir': os.path.join(input_dir, ''),
            'val_cont': True,
            'frac_post_process': 0.28633258,
            'unit_price': 29.93,
        }
    
    def test_run(self):
        guess = fisheries.execute(self.args, create_outputs=False)
        # pp.pprint(guess)

        # check harvest: 936,451
        harvest_guess = guess[0]['H_tx'][self.args['total_timesteps'] - 1].sum()
        testing.assert_approx_equal(harvest_guess, 963451.0, significant=4)

        # check spawners: 2,847,870
        spawners_guess = guess[0]['Spawners_t'][self.args['total_timesteps'] - 1]
        testing.assert_approx_equal(spawners_guess, 2847870.0, significant=3)


class TestShrimp(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': workspace_dir,
            'aoi_uri': os.path.join(input_dir, 'Shapefile_Galveston/Galveston_Subregion.shp'),
            'total_timesteps': 300,
            'population_type': 'Stage-Based',
            'sexsp': 'No',
            'harvest_units': 'Individuals',
            'do_batch': False,
            'population_csv_uri': os.path.join(input_dir, 'Inputs_Shrimp/population_params.csv'),
            'spawn_units': 'Weight',
            'total_init_recruits': 100000.0,
            'recruitment_type': 'Fixed',
            'alpha': 0,
            'beta': 0,
            'total_recur_recruits': 216000000000.0,
            'migr_cont': False,
            'migration_dir': '',
            'val_cont': False,
            'frac_post_process': 0.0,
            'unit_price': 0.0,
        }
    
    def test_run(self):
        guess = fisheries.execute(self.args, create_outputs=False)

        # check harvest: 456,424
        harvest_guess = guess[0]['H_tx'][self.args['total_timesteps'] - 1].sum()
        testing.assert_approx_equal(harvest_guess, 456424.0, significant=2)


if __name__ == '__main__':
    unittest.main()
