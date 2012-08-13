'''Testing framework for the management zone OA core. This will run an
overarching test of the core module, then compare it against a pre-edited
version.'''


import unittest
import os

from invest_natcap.overlap_analysis import overlap_analysis_mz_core

class TestMZCore(unittest.Testcase):

    def setUp
