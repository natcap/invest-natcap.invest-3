'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest

from invest_natcap.habitat_risk_assessment import hra_core
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRACore(unittest.TestCase):

    def setUp(self):

        args = {}

        args['workspace_dir'] = './data/test_out/HRA'
        args['risk_eq'] = 'Euclidean'
    
        ds_uri = './data/test_out/HRA/Intermediate/H[kelp]_S[FinfishAquacultureComm].tif'
        h_ds_uri = './data/test_out/HRA/Intermediate/Habitat_Rasters/kelp.tif'

        args['h-s'] = \
            {('kelp', 'FinfishAquacultureComm'): 
                {'E':
                    {'Spatial Overlap': {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                    'Overlap Time': {'Rating': 1.0, 'DQ': 3.0, 'Weight': 2.0},
                    #This 0.0 in the weight should remove it from the equation
                    'Intensity': {'Rating': 3.0, 'DQ': 2.0, 'Weight' : 1.0},
                    'Management Effectiveness':  {'Rating': 1.0, 'DQ': 2.0, 'Weight' : 1.0}},
                'C': {'Change in Area':  {'Rating': 3.0, 'DQ': 0.0, 'Weight' : 2.0},
                    'Change in Structure': {'Rating': 0.0, 'DQ': 1.0, 'Weight' : 1.0},
                    'Frequency of Disturbance':{'Rating': 1.0, 'DQ': 1.0, 'Weight' : 1.0},
                    },
                'DS': gdal.Open(ds_uri)
                }
           }

        args['habitats'] = \
            {'kelp': {'C':
                        {'Natural Mortality': {'Rating': 1.0, 'DQ':2.0, 'Weight':1.0},
                        'Recruitment Rate': {'Rating': 1.0, 'DQ':2.0, 'Weight':2.0},
                        'Recovery Time': {'Rating': 2.0, 'DQ':1.0, 'Weight':2.0},
                        'Connectivity Rate': {'Rating': 0.0, 'DQ':1.0, 'Weight':1.0}
                        },
                     'DS': gdal.Open(h_ds_uri)
                     }
             }

       # args['stressors'] = \
            

        self.args = args

    def test_execute(self):
        
        hra_core.execute(self.args) 
