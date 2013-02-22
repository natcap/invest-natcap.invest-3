'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest
import shutil

from invest_natcap.habitat_risk_assessment import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './data/test_out/HRA' 
        args['stressors_dir'] = './data/test_out/HRA/Input/StressorLayers'
        args['exposure_crits' = ['intensity rating', 'management effectiveness']
        args['sensitivity_crits'] = 'temporal overlap rating', \
                    'frequency of disturbance']
        args['resiliance_crits'] = ['natural mortality', 'recruitment rate']
    
        self.args = args

    def test_HabsOnly_NoShapes_smoke(self):
    '''This will use only the habitats directory as an input to overlap
    stressors, and won't attempt to pull in shapefile criteria.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        hra_preprocessor.execute(self.args)

    def test_HabsSpecies_NoShapes_smoke(self):

        self.args['do_species'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/SpeciesLayers'
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        hra_preprocessor.execute(self.args)

    def test_Missing_HabsSpecies_exception(self):
    '''Want to make sure that if neither a habitat or species is selected for
    use in overlap, that it throws an error. Should raise a 
    MissingHabitatOrSpecies exception.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = False
        self.args['do_shapes'] = False

        self.assertRaises(hra_preprocessor.MissingHabitatOrSpecies,
                        hra_preprocessor.execute, self.args)

    def test_NotEnoughCriteria_exception(self):
    '''Want to make sure that if we have at least 4 or more criteria passed
    within our 3 criteria type lists. Should raise a NotEnoughCriteria 
    exception.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resiliance_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])


        self.assertRaises(hra_preprocessor.NotEngoughCriteria,
                        hra_preprocessor.execute, self.args)

    def test_ImproperCriteraSpread_exception(self):
    '''Want to make sure that we are erroring if we don't have any criteria
    values in any of the 3 categories.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        self.args['resiliance_crits'] = []

        self.assertRaises(hra_preprocessor.ImproperCriteriaSpread,
                        hra_preprocessor.execute, self.args)

    def test_table_parse_regression(self):
    '''Given a known set of CSV's, want to make a mock up for exactly what the 
    dictionary should look like, and regression test it.'''
        
        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        expected_dict = 
            {'buffer_dict': {'FinfishAquacultureComm': 250,
                            'ShellfishAquacultureComm': 500},
            'h-s':
                {('kelp', 'finfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of natural disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': {}
                    },
                ('kelp', 'shellfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of natural disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    },
                ('eelgrass', 'finfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of natural disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    },
                ('eelgrass', 'shellfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of natural disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    }
                }
            'habitats': 
                {('kelp'):
                    {'Crit_Ratings':
                        {'natural mortality':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                        },
                     'Crit_Rasters':
                        {'recruitment rate':
                            {'Weight': 1.0, 'DQ': 1.0}
                        }
                    },
                ('eelgrass'):
                    {'Crit_Ratings':
                        {'natural mortality':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                        },
                     'Crit_Rasters':
                        {'recruitment rate':
                            {'Weight': 1.0, 'DQ': 1.0}
                        }
                    }
                },
            'stressors': 
                {('finfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'intensity':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'management effectiveness':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        }
                     'Crit_Rasters':{}
                    },
                ('shellfishaquaculturecomm'):
                    {'Crit_Ratings':
                        {'intensity':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'management_strategy_effectiveness':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters':{}
                    }
                }
        }
    
        csv_folder = './data/hra_regression_data'
        produced_dict = hra_preprocessor.parse_hra_tables(csv_folder)

        self.assertEqual(expected_dict, produced_dict)
