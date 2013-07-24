'''Test module for the hra_scratch_preprocessor module.'''


import os
import logging
import unittest
import shutil
import glob
import json

from invest_natcap.hra_scratch import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_PREPROCESSOR_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA_Scratch' 
        args['stressors_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/StressorLayers'
        args['exposure_crits'] = ['management effectiveness', 'intensity_rating']
        args['sensitivity_crits'] = ['temporal overlap', \
                    'frequency of disturbance']
        args['resilience_crits'] = ['recruitment rate', 'natural mortality']
    
        self.args = args

    def test_HabsOnly_NoShapes_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and won't attempt to pull in shapefile criteria.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

        hra_preprocessor.execute(self.args)
    
    def test_HabsOnlyShape_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and will atempt to use a single shapefile criteria with
        eelgrass and recruitment rate.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'
        self.args['criteria_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria'

        hra_preprocessor.execute(self.args)

    @unittest.skip("For later testing.")
    def test_HabsSpecies_NoShapes_smoke(self):

        self.args['species_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA/Input/SpeciesLayers'
        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

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

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resilience_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])

        self.assertRaises(hra_preprocessor.NotEnoughCriteria,
                        hra_preprocessor.execute, self.args)
    
    def test_Improper_Crit_FileStruct(self):
        '''Since the folder structure for the criteria shapefiles must be in an
        explicit form, want to check that it will error if given an incorrect
        folder setup.'''

        crit_uri = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria_Bad_Struct'

        self.assertRaises(IOError, hra_preprocessor.make_crit_shape_dict,
                    crit_uri)
    
    def test_make_crit_dict_regression(self):
        '''This should specifically test the make_crit_shape_dict function in
        hra_preprocessor. This will get called by both preprocessor and
        non-core. Want to check against the dictionary of what we think it
        should be.'''

        shp_crit_dir = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria'

        expected_dict = \
            {'h_s_e': {},
             'h': {'kelp':
                    {'recruitment rate': 
                        '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria/Resilience/kelp_recruitment_rate.shp'
                    }
                  },
             'h_s_c': {}
            }

        produced_dict = hra_preprocessor.make_crit_shape_dict(shp_crit_dir)

        self.maxDiff = None
        self.assertEqual(expected_dict, produced_dict)

    def test_UnexpectedString_exception(self):
        '''Want to make sure that preproc will throw an exception if a CSV is
        passed which contains strings or null values where there should be
        floats for use in calculation'''

        test_CSV = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/habitat_stressor_ratings_null_vals/kelp_ratings.csv'
        empty_dict = {}

        self.assertRaises(hra_preprocessor.UnexpectedString,
                        hra_preprocessor.parse_overlaps, test_CSV, empty_dict, 
                                                                    empty_dict, empty_dict)

    def test_remove_zero_reg(self):
        '''We want to test the preprocessor functionality to properly remove any
        subdictionaries that have 0 rating values. We have already raised exceptions
        elsewhere for zero dq's or weights.'''

        h_s_c = \
            {('kelp', 'FinfishAquacultureComm'):
                {'Crit_Ratings':
                    {'temporal overlap':
                        {'Rating': 0.0, 'DQ': 1.0, 'Weight': 1.0},
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
            }
        habs = \
            {('kelp'):
                {'Crit_Ratings':
                    {'natural mortality':
                        {'Rating': 0.0, 'DQ': 1.0, 'Weight': 1.0},
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
            }
        h_s_e = \
            {('kelp', 'FinfishAquacultureComm'):
                {'Crit_Ratings':
                    {'intensity rating':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':{}
                },
            ('kelp', 'ShellfishAquacultureComm'):
                {'Crit_Ratings':
                    {'intensity rating':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                'Crit_Rasters':{}
                },
            ('eelgrass', 'FinfishAquacultureComm'):
                {'Crit_Ratings':
                    {'intensity rating':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':{}
                },
            ('eelgrass', 'ShellfishAquacultureComm'):
                {'Crit_Ratings':
                    {'intensity rating':
                        {'Rating': 0.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                'Crit_Rasters':{}
                }
            }
        
        #Anything that has a 0 in the ratings score should have the entire criteria
        #removed from the dictionary.
        exp_dict_h = habs.copy()
        exp_dict_h_s_e = h_s_e.copy()
        exp_dict_h_s_c = h_s_c.copy()

        #The criteria which should be removed automagically when run through the
        #function.
        del exp_dict_h['kelp']['Crit_Ratings']['natural mortality']
        del exp_dict_h_s_e[('eelgrass', 'ShellfishAquacultureComm')]['Crit_Ratings']['intensity rating']
        del exp_dict_h_s_c[('kelp', 'FinfishAquacultureComm')]['Crit_Ratings']['temporal overlap']

        #If function works correctly, should edit our versions of the three dicts.
        hra_preprocessor.zero_check(h_s_c, h_s_e, habs)

        self.maxDiff = None
        self.assertEqual(exp_dict_h, habs)
        self.assertEqual(exp_dict_h_s_e, h_s_e)
        self.assertEqual(exp_dict_h_s_c, h_s_c)

    def test_error_checking_reg(self):
        '''Want to test the error_checking functionality that exists for individual
        lines of preprocessor's parse.

        There should be an error thrown for each of the following:
        
            Rating- Can either be the explicit string 'SHAPE', which would
                be placed automatically by HRA_Preprocessor, or a float.
                ERROR: UnexpectedString- for string != 'SHAPE'
            Weight- Must be a float (or an int), but cannot be 0.
                ERROR: ZeroDQWeightValue- if string, or anything not castable 
                to float, or 0.
            DataQuality- Most be a float (or an int), but cannot be 0.
                ERROR: ZeroDQWeightValue- if string, or anything not castable
                to float, or 0.
            Exp/Cons- Most be the string 'E' or 'C'.
                ERROR: ImproperECSelection- if string that isn't one of the 
                acceptable ones, or ANYTHING else.
        '''
        #Takes name parameters in order to throw an informative error. Not essential
        #for the inner workings of the function.
        hab = 'kelp'
        stress = 'FFA'

        good_line = ['Criteria', 'SHAPE', '1', '1', 'E']

        line_bad_rating = ['Criteria', 'BADWOLF', '1', '1', 'E']
        line_bad_weight = ['Criteria', 'SHAPE', '0', '1', 'E']
        line_bad_dq = ['Criteria', 'SHAPE', '1', 'DoodleBug', 'E']
        line_bad_ec = ['Criteria', 'SHAPE', '0', '1', 'Jeepers']

        hra_preprocessor.error_check(good_line, hab, stress)

        self.assertRaises(hra_preprocessor.UnexpectedString,
                        hra_preprocessor.error_check, line_bad_rating, hab, stress)

        self.assertRaises(hra_preprocessor.ZeroDQWeightValue,
                        hra_preprocessor.error_check, line_bad_weight, hab, stress)

        self.assertRaises(hra_preprocessor.ZeroDQWeightValue,
                        hra_preprocessor.error_check, line_bad_dq, hab, stress)
                        
        self.assertRaises(hra_preprocessor.ImproperECSelection,
                        hra_preprocessor.error_check, line_bad_ec, hab, stress)
