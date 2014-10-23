import unittest
import pprint

from numpy import testing
import numpy as np

import fisheries_model as model

pp = pprint.PrettyPrinter(indent=4)


class TestInitializeVars(unittest.TestCase):
    def setUp(self):
        self.sample_vars = {
            #'workspace_dir': 'path/to/workspace_dir',
            #'aoi_uri': 'path/to/aoi_uri',
            'total_timesteps': 100,
            'population_type': 'Stage-Based',
            'sexsp': 2,
            'spawn_units': 'Weight',
            'total_init_recruits': 100.0,
            'recruitment_type': 'Ricker',
            'alpha': 32.4,
            'beta': 54.2,
            'total_recur_recruits': 92.1,
            'migr_cont': True,
            'harv_cont': True,
            'harvest_units': 'Individuals',
            'frac_post_process': 0.5,
            'unit_price': 5.0,

            # Pop Params
            #'population_csv_uri': 'path/to/csv_uri',
            'Survnaturalfrac': np.ones([2, 2, 2]),  # Regions, Sexes, Classes
            'Classes': np.array(['larva', 'adult']),
            'Vulnfishing': np.array([[0.5, 0.5], [0.5, 0.5]]),
            'Maturity': np.array([[0.0, 1.0], [0.0, 1.0]]),
            'Duration': np.array([[2, 3], [2, 3]]),
            'Weight': np.array([[0.1, 1.0], [0.1, 2.0]]),
            'Fecundity': np.array([[0.0, 1.0], [0.0, 1.0]]),
            'Regions': np.array(['r1', 'r2']),
            'Exploitationfraction': np.array([0.25, 0.5]),
            'Larvaldispersal': np.array([0.75, 0.75]),

            # Mig Params
            #'migration_dir': 'path/to/mig_dir',
            'Migration': [np.eye(2), np.eye(2)]
        }

    def test_calc_survtotalfrac(self):
        # Test very simple
        self.sample_vars['Survnaturalfrac'] = np.array([[[1, 0.5], [0.5, 1]], [[2, 1], [1, 2]]])
        self.sample_vars['Exploitationfraction'] = np.array([1.0, 2.0])
        self.sample_vars['Vulnfishing'] = np.array([[1.0, 2.0], [2.0, 1.0]])
        check = np.array([[[0, -0.5], [-0.5, 0]], [[-2, -3], [-3, -2]]])
        guess = model._calc_survtotalfrac(self.sample_vars)
        # print "Guess"
        # pp.pprint(guess)
        # print "Check"
        # pp.pprint(check)
        testing.assert_array_equal(guess, check)

    def test_p_g_survtotalfrac(self):
        # Test simple
        self.sample_vars['Survtotalfrac'] = np.array([[[1, 0.5], [0.5, 1]], [[2, 1], [1, 2]]])
        self.sample_vars['Exploitationfraction'] = np.array([1.0, 2.0])
        self.sample_vars['Vulnfishing'] = np.array([[1.0, 2.0], [2.0, 1.0]])
        self.sample_vars['Duration'] = np.array([[1.0, 2.0], [1.0, 3.0]])
        G_check = np.array([[[np.nan, 1.0/6], [0.5, np.nan]], [[2.0, np.nan], [np.nan, 8.0/7]]])
        P_check = np.array([[[np.nan, 1.0/3], [0.0, np.nan]], [[0.0, np.nan], [np.nan, 6.0/7]]])
        G_guess, P_guess = model._calc_p_g_survtotalfrac(self.sample_vars)
        # print "G_Guess"
        # pp.pprint(G_guess)
        # print "G_Check"
        # pp.pprint(G_check)
        # print "P_Guess"
        # pp.pprint(P_guess)
        # print "P_Check"
        # pp.pprint(P_check)
        testing.assert_array_equal(P_guess, P_check)

    def test_initialize_vars(self):
        # vars_dict = model.initialize_vars(self.sample_vars)
        # pp.pprint(vars_dict['Survtotalfrac'])
        # pp.pprint(vars_dict['G_survtotalfrac'])
        # pp.pprint(vars_dict['P_survtotalfrac'])
        pass


class TestSetRecruitmentFunc(unittest.TestCase):
    def setUp(self):
        self.sample_vars = {
            #'workspace_dir': 'path/to/workspace_dir',
            #'aoi_uri': 'path/to/aoi_uri',
            'total_timesteps': 100,
            'population_type': 'Stage-Based',
            'sexsp': 2,
            'spawn_units': 'Weight',
            'total_init_recruits': 100.0,
            'recruitment_type': 'Ricker',
            'alpha': 32.4,
            'beta': 54.2,
            'total_recur_recruits': 92.1,
            'migr_cont': True,
            'harv_cont': True,
            'harvest_units': 'Individuals',
            'frac_post_process': 0.5,
            'unit_price': 5.0,

            # Pop Params
            #'population_csv_uri': 'path/to/csv_uri',
            'Survnaturalfrac': np.ones([2, 2, 2]),  # Regions, Sexes, Classes
            'Classes': np.array(['larva', 'adult']),
            'Vulnfishing': np.array([[0.5, 0.5], [0.5, 0.5]]),
            'Maturity': np.array([[0.0, 1.0], [0.0, 1.0]]),
            'Duration': np.array([[2, 3], [2, 3]]),
            'Weight': np.array([[0.1, 1.0], [0.1, 2.0]]),
            'Fecundity': np.array([[0.0, 1.0], [0.0, 1.0]]),
            'Regions': np.array(['r1', 'r2']),
            'Exploitationfraction': np.array([0.25, 0.5]),
            'Larvaldispersal': np.array([0.75, 0.75]),

            # Mig Params
            #'migration_dir': 'path/to/mig_dir',
            'Migration': [np.eye(2), np.eye(2)]
        }

    def test_spawners(self):
        def create_Spawners(Matu, Weight):
            return lambda N_prev: (N_prev * Matu * Weight).sum()

        N_prev = np.array(
            [[[5.0, 10.0], [2.0, 4.0]], [[4.0, 8.0], [1.0, 2.0]]])
        Matu = self.sample_vars['Maturity']
        Weight = self.sample_vars['Weight']
        f = create_Spawners(Matu, Weight)
        check = 30
        guess = f(N_prev)
        # print "Guess"
        # pp.pprint(guess)
        testing.assert_equal(guess, check)

    def test_set_recru_func(self):
        ### IMPLEMENT THIS TOMORROW

        pass


if __name__ == '__main__':
    unittest.main()
