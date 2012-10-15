'''This will be the test module for the non-core portion of Habitat Risk
Assessment.'''

import os
import unittest
import logging

import invest_test_core

from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra

LOGGER = logging.getLogger('hra_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './data/test_out/HRA' 
        args['habitat_dir'] = '../../HabitatRiskAssess/Input/HabitatLayers'
        args['stressors_dir'] = '../../HabitatRiskAssess/Input'

        args['grid_size'] = 500
        args['risk_eq'] = 'Euclidean'

        #Want to have some pairs that don't include some stressors to make sure
        #that the model can handle some things not being included all of the time.
        args['ratings'] = {
            ('kelp', 'FinfishAquacultureComm'): {'E':
                    {'Spatial Overlap': {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                    'Overlap Time': {'Rating': 1.0, 'DQ': 3.0, 'Weight': 2.0},
                    #This 0.0 in the weight should remove it from the equation
                    'Intensity': {'Rating': 3.0, 'DQ': 2.0, 'Weight' : 0.0},
                    'Management Effectiveness':  {'Rating': 1.0, 'DQ': 2.0, 'Weight' : 1.0}},
                'C': {'Change in Area':  {'Rating': 3.0, 'DQ': 1.0, 'Weight' : 2.0},
                    'Change in Structure': {'Rating': 2.0, 'DQ': 1.0, 'Weight' : 1.0},
                    'Frequency of Disturbance':{'Rating': 1.0, 'DQ': 1.0, 'Weight' : 1.0},
                    #Here would be the biotic stressors. But need to figure out
                    #how to know difference between biotic and abiotic. Could
                    #just put the impetus on the user.
                    }
                }
           }

        self.args =args

    def test_ALL(self)

        hra.execute(self.args)
