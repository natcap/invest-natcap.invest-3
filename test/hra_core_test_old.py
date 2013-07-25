'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest
import shutil
import math

from invest_natcap.habitat_risk_assessment import hra_core
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRACore(unittest.TestCase):

    def setUp(self):

        LOGGER.debug('SHOW THE CWD:' + str(os.getcwd()))
        
        args = {}

        args['workspace_dir'] = './invest-data/test/data/test_out/HRA/Test1'
    
        #For purposes of running test independently of HRA non-core, need to
        #delete current intermediate and output folders
        out_dir = os.path.join(args['workspace_dir'], 'Output')
        inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
   
        overlap_dir = './invest-data/test/data/test_out/HRA/Reg_Inputs/Intermediate/Overlap_Rasters'

        for folder in [out_dir, inter_dir]:
            if (os.path.exists(folder)):
                shutil.rmtree(folder) 

            os.makedirs(folder)
        
        #For the basic runs, include both the 'Crit_Ratings' and 'Crit_Rasters'
        #subdictionaries. For individual tests, remove them each and try.
        args['h-s'] = \
            {('kelp', 'finfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'change_in_area':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                           './invest-data/test/data/test_out/HRA/Criteria_Rasters/kelp_finfishaquaculturecomm_change_in_area.tif'
                        }
                    },
                 'DS': 
                    os.path.join(overlap_dir, 'H[kelp]_S[FinfishAquacultureComm].tif')
                },
            ('kelp', 'shellfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'change_in_area':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/kelp_shellfishaquaculturecomm_change_in_area.tif'
                        }
                    },
                 'DS': 
                    os.path.join(overlap_dir, 'H[kelp]_S[ShellfishAquacultureComm].tif')
               },
           ('eelgrass', 'finfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'change_in_area':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/eelgrass_finfishaquaculturecomm_change_in_area.tif'
                        }
                    },
                 'DS': 
                    os.path.join(overlap_dir, 'H[eelgrass]_S[FinfishAquacultureComm].tif')
                },
           ('eelgrass', 'shellfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'change_in_area':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/eelgrass_shellfishaquaculturecomm_change_in_area.tif'
                        }
                    },
                 'DS': 
                    os.path.join(overlap_dir, 'H[eelgrass]_S[ShellfishAquacultureComm].tif')
                }
            }
         
        args['habitats'] = \
            {('kelp'):
                {'Crit_Ratings':
                    {'natural_mortality':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'conectivity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'connectivity_rating':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/kelp_connectivity_rating.tif'
                        }
                    },
                 'DS': 
                    './invest-data/test/data/test_out/HRA/Reg_Inputs/Intermediate/Habitat_Rasters/kelp.tif'
                },
            ('eelgrass'):
                {'Crit_Ratings':
                    {'natural_mortality':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'conectivity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'connectivity_rating':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/eelgrass_connectivity_rating.tif'
                        }
                    },
                 'DS': 
                    './invest-data/test/data/test_out/HRA/Reg_Inputs/Intermediate/Habitat_Rasters/eelgrass.tif'
                }
            }
        args['stressors'] = \
            {('finfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'intensity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management_strategy_effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'new_stresscrit':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/finfishaquaculturecomm_new_stresscrit.tif'
                        }
                    },
                 'DS': 
                    './invest-data/test/data/test_out/HRA/Reg_Inputs/Intermediate/Stressor_Rasters/FinfishAquacultureComm_buff.tif'
                },
            ('shellfishaquaculturecomm'):
               {'Crit_Ratings':
                    {'intensity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management_strategy_effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {'new_stresscrit':
                        {'Weight': 1.0, 'DQ': 1.0, 
                        'DS':
                            './invest-data/test/data/test_out/HRA/Criteria_Rasters/shellfishaquaculturecomm_new_stresscrit.tif'
                        }
                    },
                'DS': 
                    './invest-data/test/data/test_out/HRA/Reg_Inputs/Intermediate/Stressor_Rasters/ShellfishAquacultureComm_buff.tif'
                } 
            }
        self.args = args

    def test_euc_smoke(self):
        '''This will test the standard run in which we would have Euclidean
        risk with a maximum risk value of 3.
        '''
        #in an average test run, would likely have Euclidean risk, and a max
        #rating of 3. The max risk would therefore be as seen below.
        self.args['risk_eq'] = 'Euclidean'
        self.args['max_risk'] = math.sqrt((3-1)**2 + (3-1)**2)

        hra_core.execute(self.args)
    
    def test_mult_smoke(self):
        '''This tests the alternate risk equation in which we would use a
        multiplicative risk equation, but would still have a max risk value of 3.
        '''
        #Now, do one that uses multiplicative risk. Still want to use a max
        #rating of 3 as a test.
        self.args['risk_eq'] = 'Multiplicative'
        self.args['max_risk'] = 3

        hra_core.execute(self.args)

    def test_diff_num_crits_smoke(self):
        '''Want to test that the model will still run if we have different numbers of
        criteria, but the model would have (hypothetically) passed the minimum 
        required to avoid an exception throw in hra non-core. '''

        #Still need to have standard risk calculation in order to get
        #the whole core to run
        self.args['risk_eq'] = 'Euclidean'
        self.args['max_risk'] = math.sqrt((3-1)**2 + (3-1)**2)


        LOGGER.debug(self.args['h-s'])
        #Want to take out a single criteria from one of the habitat-stressor
        #pairs, in order to make sure that core can run when things have
        #different numbers of criteria
        del self.args['h-s'][('kelp', 'finfishaquaculturecomm')]['Crit_Ratings']\
                ['temporal_overlap']

        hra_core.execute(self.args)

    def test_no_rast_dict(self):
        '''Want to test the case where we have a complete dictionary, but one of the
        h-s pairs within the dictionary does not contain a rasters dictionary at all.
        This should be a viable run, since Crit_Rasters would not get built if there
        were no qualifying shapefile criteria for that pairing.'''

        #Still need standard risk calc stuff.
        self.args['risk_eq'] = 'Euclidean'
        self.args['max_risk'] = math.sqrt((3-1)**2 + (3-1)**2)

        #Want to make sure that if we don't have raster criteria, that the core
        #will still run.
        self.args['h-s'][('kelp', 'finfishaquaculturecomm')]['Crit_Rasters'] = {}
        
        hra_core.execute(self.args)

