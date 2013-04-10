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
        args['stressors_dir'] = './data/hra_regression_data/Input/StressorLayers'
        args['exposure_crits'] = ['intensity rating rating', 'management effectiveness']
        args['sensitivity_crits'] = ['temporal overlap rating', \
                    'frequency of disturbance']
        args['resiliance_crits'] = ['natural mortality', 'recruitment rate']
    
        self.args = args

    def test_HabsOnly_NoShapes_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and won't attempt to pull in shapefile criteria.'''

        self.args['habitats_dir'] = './data/hra_regression_data/Input/HabitatLayers'

        hra_preprocessor.execute(self.args)

    def test_HabsOnlyShape_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and will atempt to use a single shapefile criteria with
        eelgrass and recruitment_rate.'''

        self.args['habitats_dir'] = './data/hra_regression_data/Input/HabitatLayers'
        self.args['criteria_dir'] = './data/hra_regression_data/Shape_Criteria'

        hra_preprocessor.execute(self.args)

    @unittest.skip("For later testing.")
    def test_HabsSpecies_NoShapes_smoke(self):

        self.args['species_dir'] = './data/test_out/HRA/Input/SpeciesLayers'
        self.args['habitats_dir'] = './data/test_out/HRA/Input/HabitatLayers'

        hra_preprocessor.execute(self.args)

    def test_Missing_HabsSpecies_exception(self):
        '''Want to make sure that if neither a habitat or species is selected for
        use in overlap, that it throws an error. Should raise a 
        MissingHabitatOrSpecies exception.'''

        self.assertRaises(hra_preprocessor.MissingHabitatsOrSpecies,
                        hra_preprocessor.execute, self.args)

    def test_NotEnoughCriteria_exception(self):
        '''Want to make sure that if we have at least 4 or more criteria passed
        within our 3 criteria type lists. Should raise a NotEnoughCriteria 
        exception.'''

        self.args['habitats_dir'] = './data/test_out/HRA/Input/HabitatLayers'

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resiliance_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])


        self.assertRaises(hra_preprocessor.NotEnoughCriteria,
                        hra_preprocessor.execute, self.args)

    def test_ImproperCriteraSpread_exception(self):
        '''Want to make sure that we are erroring if we don't have any criteria
        values in any of the 3 categories.'''

        self.args['habitats_dir'] = './data/test_out/HRA/Input/HabitatLayers'

        self.args['resiliance_crits'] = []

        self.assertRaises(hra_preprocessor.ImproperCriteriaSpread,
                        hra_preprocessor.execute, self.args)

    def test_table_parse_regression(self):
       '''Want to specifically test the dictionary making function that gets
       called in hra_preprocessor from hra. There will be a TON of things in
       this one. Just need to make sure that the folder we're testing against
       had the proper params enabled within the dir_names.txt file.'''

        csv_folder = './data/hra_regression_data/habitat_stressor_ratings'

        expected_dict = \
            {'habitats_dir': './data/hra_regression_data/Input/HabitatLayers',
            'stressors_dir': './data/hra_regression_data/StressorLayers',
            'criteria_dir': './data/hra_regression_data/Shape_Criteria',
            'buffer_dict': {'FinfishAquacultureComm': 250.0,
                            'ShellfishAquacultureComm': 500.0},
            'h-s':
                {('kelp', 'FinfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': {}
                    },
                ('kelp', 'ShellfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    },
                ('eelgrass', 'FinfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    },
                ('eelgrass', 'ShellfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'temporal overlap':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'frequency of disturbance':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    }
                },
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
                {('FinfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'intensity rating':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'management effectiveness':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                     'Crit_Rasters':{}
                    },
                ('ShellfishAquacultureComm'):
                    {'Crit_Ratings':
                        {'intensity rating':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                         'management effectiveness':
                            {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters':{}
                    }
                }
            }
    
        produced_dict = hra_preprocessor.parse_hra_tables(csv_folder)
        
        self.maxDiff=None
        self.assertEqual(expected_dict, produced_dict)

    def test_make_crit_dict_regression(self):
        '''This should specifically test the make_crit_shape_dict function in
        hra_preprocessor. This will get called by both preprocessor and
        non-core. Want to check against the dictionary of what we think it
        should be.'''

        shp_crit_dir = './data/hra_regression_data/Shape_Criteria'

        expected_dict = \
            {'h-s': {},
             'h': {'kelp':
                    {'recruitment_rate': 
                        './data/hra_regression_data/Shape_Criteria/Resilience/kelp_recruitment_rate.shp'
                    }
                  }
             's': {}
            }

        produced_dict = hra_preprocessor.make_crit_shape_dict(shp_crit_dir)

        self.maxDiff = None
        self.assertEqual(expected_dict, produced_dict)
