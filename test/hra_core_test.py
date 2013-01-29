'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest
import shutil

from invest_natcap.habitat_risk_assessment import hra_core
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRACore(unittest.TestCase):

    def setUp(self):

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
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                            H[kelp]_S[FinfishAquacultureComm].tif')
                },
            ('kelp', 'shellfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                           H[kelp]_S[ShellfishAquacultureComm].tif')
               },
           ('eelgrass', 'finfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                           H[kelp]_S[ShellfishAquacultureComm].tif')
                },
           ('eelgrass', 'shellfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'temporal_overlap':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'frequency_of_natural_disturbance':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                           H[kelp]_S[ShellfishAquacultureComm].tif')
                }
            }
         
        args['habitats'] = \
            {('kelp'):
                {'Crit_Ratings':
                    {'natural_mortality':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'conectivity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                            Habitat_Rasters/kelp.tif')
                },
            ('eelgrass'):
                {'Crit_Ratings':
                    {'natural_mortality':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'conectivity':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                            Habitat_Rasters/eelgrass.tif')
                }
            }
        args['stressors'] = \
            {('finfishaquaculturecomm'):
                {'Crit_Ratings':
                    {'intensity':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'management_strategy_effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                 'Crit_Rasters':
                    {},
                 'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                            Stressor_Rasters/FinfishAquacultureComm.tif')
                },
            ('shellfishaquaculturecomm'):
               {'Crit_Ratings':
                    {'intensity':
                        {'Rating': 1.0, 'DQ' 1.0, 'Weight': 1.0},
                     'management_strategy_effectiveness':
                        {'Rating': 1.0, 'DQ': 1.0, 'Weight': 1.0}
                    },
                'Crit_Rasters':
                    {},
                'DS': gdal.Open('./data/test_out/HRA/Intermediate/\
                            Stressor_Rasters/ShellfishAquacultureComm.tif')
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

