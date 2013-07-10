'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest
import shutil
import glob
import json

from invest_natcap.habitat_risk_assessment import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA' 
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
        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA/Input/HabitatLayers'

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

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA/Input/HabitatLayers'

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resilience_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])


        self.assertRaises(hra_preprocessor.NotEnoughCriteria,
                        hra_preprocessor.execute, self.args)

    def test_ImproperCriteraSpread_exception(self):
        '''Want to make sure that we are erroring if we don't have any criteria
        values in any of the 3 categories.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA/Input/HabitatLayers'

        self.args['resilience_crits'] = []

        self.assertRaises(hra_preprocessor.ImproperCriteriaSpread,
                        hra_preprocessor.execute, self.args)

    def test_table_parse_regression(self):
        '''Want to specifically test the dictionar making function that gets
        called in hra_preprocessor from hra. There will be a TON of things in
        this one. Just need to make sure that the folder we're testing against
        had the proper params enabled within the dir_names.txt file.'''

        csv_folder = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/habitat_stressor_ratings'
       
        #since the file paths are coming in through the JSON import, they will
        #be unicode
        expected_dict = \
            {u'habitats_dir': u'/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers',
            u'stressors_dir': u'/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/StressorLayers',
            u'criteria_dir': u'/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria',
            'buffer_dict': {'FinfishAquacultureComm': 1000.0,
                            'ShellfishAquacultureComm': 2000.0},
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
                         'recruitment rate':
                            {'Rating': 1.0, 'Weight': 1.0, 'DQ': 1.0}
                        },
                     'Crit_Rasters': {}
                        
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

        shp_crit_dir = './invest-data/test/data/hra_regression_data/Shape_Criteria'

        expected_dict = \
            {'h-s': {},
             'h': {'kelp':
                    {'recruitment rate': 
                        './invest-data/test/data/hra_regression_data/Shape_Criteria/Resilience/kelp_recruitment_rate.shp'
                    }
                  },
             's': {}
            }

        produced_dict = hra_preprocessor.make_crit_shape_dict(shp_crit_dir)

        self.maxDiff = None
        self.assertEqual(expected_dict, produced_dict)

    def test_remove_zero_reg(self):
        '''We want to test the preprocessor functionality to properly remove any
        subdictionaries that have 0 rating values, and raise exceptions if there
        are 0's in either DQ or Weight.'''

        curr_dict_zeros = \
            {u'habitats_dir': u'./invest-data/test/data/hra_regression_data/Input/HabitatLayers',
            u'stressors_dir': u'./invest-data/test/data/hra_regression_data/Input/StressorLayers',
            u'criteria_dir': u'./invest-data/test/data/hra_regression_data/Shape_Criteria',
            'buffer_dict': {'FinfishAquacultureComm': 250.0,
                            'ShellfishAquacultureComm': 500.0},
            'h-s':
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
                },
            'habitats': 
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
    
        #Anything that has a 0 in the ratings score should have the entire criteria
        #removed from the dictionary.
        expected_dict = curr_dict_zeros.copy()
        del expected_dict['h-s'][('kelp', 'FinfishAquacultureComm')]['Crit_Ratings']['temporal overlap']
        del expected_dict['habitats']['kelp']['Crit_Ratings']['natural mortality']

        #I...think the scope of this should change our version of curr_dict_zeros
        hra_preprocessor.zero_null_val_check(curr_dict_zeros)

        self.maxDiff = None
        self.assertEqual(expected_dict, curr_dict_zeros)

        
        #Now want to try to get it to throw the ZeroDQWeightValue error
        curr_dict_zeros['habitats']['eelgrass']['Crit_Ratings']['natural mortality']['DQ'] = ''
        curr_dict_zeros['stressors']['FinfishAquacultureComm']['Crit_Ratings']['intensity rating']['DQ'] = 0

        self.assertRaises(hra_preprocessor.ZeroDQWeightValue,
                        hra_preprocessor.zero_null_val_check, curr_dict_zeros)

    def test_UnexpectedString_exception(self):
        '''Want to make sure that preproc will throw an exception if a CSV is
        passed which contains strings or null values where there should be
        floats for use in calculation'''

        test_CSV = './invest-data/test/data/hra_regression_data/habitat_stressor_ratings_null_vals/kelp_overlap_ratings.csv'

        self.assertRaises(hra_preprocessor.UnexpectedString,
                        hra_preprocessor.parse_habitat_overlap, test_CSV)
  
    def test_Improper_Crit_FileStruct(self):
        '''Since the folder structure for the criteria shapefiles must be in an
        explicit form, want to check that it will error if given an incorrect
        folder setup.'''

        crit_uri = './invest-data/test/data/hra_regression_data/Shape_Criteria_Bad_Struct'

        self.assertRaises(IOError, hra_preprocessor.make_crit_shape_dict,
                    crit_uri)

    def test_overall_regression(self):
        '''This is the overarching regression test for the CSV outputs within
        preprocessor. We will use the habitats folder that we already have set
        up and compare it to the "cealn run" folder that it the output just
        after those inputs have been used.'''

        self.args['habitats_dir'] = './invest-data/test/data/hra_regression_data/Input/HabitatLayers'
        self.args['criteria_dir'] = './invest-data/test/data/hra_regression_data/Shape_Criteria'

        #Run to create the outputs.
        hra_preprocessor.execute(self.args)
    
        #We know that the output will be within the workspace directory
        result_dir = os.path.join(self.args['workspace_dir'], 'habitat_stressor_ratings')

        r_file_list = glob.glob(os.path.join(result_dir, '*'))

        #Know the location of our clean run directory, get the files within,
        #and check that they exist, and are correct within result_dir
        clean_dir = './invest-data/test/data/hra_regression_data/habitat_stressor_ratings_clean'

        c_file_list = glob.glob(os.path.join(clean_dir, '*.csv'))

        for c_uri in c_file_list:

            c_name = os.path.basename(c_uri)
            expected_name = os.path.join(result_dir, c_name)

            c_file = open(c_uri, 'rU')
            r_file = open(expected_name, 'rU')
          
            self.maxDiff = None
            self.assertEqual(c_file.readlines(), r_file.readlines())

            #Want to check off that we know that file was good for expected
            #results
            r_file_list.remove(expected_name)
        
        #At this point, we should just have the dir_names.txt file left in the
        #file list of the created dictionary.
        c_json_uri = os.path.join('./invest-data/test/data/hra_regression_data/habitat_stressor_ratings_clean/dir_names.txt')
        c_dict = json.load(open(c_json_uri))

        r_expected_uri = os.path.join(result_dir, 'dir_names.txt')
        r_dict = json.load(open(r_expected_uri))

        #This has issues with relative paths vs the full path. We are just going
        #to check that all the same pieces are there, rather than having the
        #paths be identical. Assume the one of the other asserts would pick this up.
        self.assertEqual(c_dict.keys(), r_dict.keys())

        r_file_list.remove(r_expected_uri)

        #There should be no files left within the workspace directory
        self.assertEqual(len(r_file_list), 0)
