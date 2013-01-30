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

        args['workspace_dir'] = './data/test_out/HRA'
    
        #For purposes of running test independently of HRA non-core, need to
        #delete current intermediate and output folders
        out_dir = os.path.join(args['workspace_dir'], 'Output')

        if (os.path.exists(out_dir)):
            shutil.rmtree(out_dir) 

        os.makedirs(out_dir)
        
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
                            gdal.Open('./data/test_out/HRA/Criteria_Rasters/kelp_finfishaquaculturecomm_change_in_area.tif')
                        }
                    },
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/H[kelp]_S[FinfishAquacultureComm].tif')
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
                            gdal.Open('./data/test_out/HRA/Criteria_Rasters/kelp_shellfishaquaculturecomm_change_in_area.tif')
                        }
                    },
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/H[kelp]_S[ShellfishAquacultureComm].tif')
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
                            gdal.Open('./data/test_out/HRA/Criteria_Rasters/eelgrass_finfishaquaculturecomm_change_in_area.tif')
                        }
                    },
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/H[kelp]_S[ShellfishAquacultureComm].tif')
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
                            gdal.Open('./data/test_out/HRA/Criteria_Rasters/eelgrass_shellfishaquaculturecomm_change_in_area.tif')
                        }
                    },
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/H[kelp]_S[ShellfishAquacultureComm].tif')
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
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/Habitat_Rasters/kelp.tif')
                },
            ('eelgrass'):
                {'Crit_Ratings':
                    {'natural_mortality':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'conectivity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/Habitat_Rasters/eelgrass.tif')
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
                 'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/Stressor_Rasters/FinfishAquacultureComm_buff.tif')
                },
            ('shellfishaquaculturecomm'):
               {'Crit_Ratings':
                    {'intensity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0},
                     'management_strategy_effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                'DS': 
                    gdal.Open('./data/test_out/HRA/Intermediate/Stressor_Rasters/ShellfishAquacultureComm_buff.tif')
                } 
            }
        self.args = args

    def test_euc_execute(self):
       
        #in an average test run, would likely have Euclidean risk, and a max
        #rating of 3. The max risk would therefore be as seen below.
        self.args['risk_eq'] = 'Euclidean'
        self.args['max_risk'] = math.sqrt((3-1)**2 + (3-1)**2)

        hra_core.execute(self.args)

    def test_mult_execute(self):

        #Now, do one that uses multiplicative risk. Still want to use a max
        #rating of 3 as a test.
        self.args['risk_eq'] = 'Multiplicative'
        self.args['max_risk'] = 3

        hra_core.execute(self.args)

    def test_diff_num_crits(self):
        
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
        
        #Still need standard risk calc stuff.
        self.args['risk_eq'] = 'Euclidean'
        self.args['max_risk'] = math.sqrt((3-1)**2 + (3-1)**2)

        #Want to make sure that if we don't have raster criteria, that the core
        #will still run.
        del self.args['h-s'][('kelp', 'finfishaquaculturecomm')]['Crit_Rasters']
        
        hra_core.execute(self.args)

    def test_zero_val_ratings(self):
        '''We know that the core should never recieve anything with a DQ or W
        of 0, since that would NaN most of the equations. But, want to make
        sure that 0 values in the ratings will be okay. There should
        automagically be some in the rasters, since we will have nodata
        values, but check for the single ratings values.'''

        #IF RATING IS 0, NEED TO REMOVE THAT DICTIONARY, ELSE WE WILL END UP
        #STILL ADDING THE DQ/W TO THE CALCULATIONS AS 1/DQ OR 1/DQ*W

        #So....this test should never happen. Hypothetically.
        self.args['h-s']['Crit_Ratings'][('kelp', 'finfishaquaculturecomm')]\
            ['temporal_overlap']['Rating'] = 0.0
        
        hra_core.execute(self)
