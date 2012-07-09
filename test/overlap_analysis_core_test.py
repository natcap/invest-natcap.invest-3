'''Testing framework specifically for the overlap analysis core. This will test
the individual functions of the core, as well as running a comprehensive test for the
entire class.
'''

import os
import unittest

import invest_test_core
from invest_natcap.overlap_analysis import overlap_analysis_core

class TestOverlapAnalysisCore(unittest.TestCase):

    def setUp(self):
        
        args = {}
        args['workspace'] = './data/test_out/Overlap'
        args['intermediate'] = os.path.join(args['workspace'], 'Intermediate')