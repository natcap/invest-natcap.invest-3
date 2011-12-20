import os, sys
import unittest

from nose.exc import SkipTest

import timber

class TestInvestTimberCore(unittest.TestCase):
    def test_timber_model(self):
        raise SkipTest("haven't refactored this test yet")
        args = {'output_dir': '../../test_data/timber',
                'timber_shape_uri': '../../timber/input/plantation.shp',
                'attr_table_uri': '../../timber/input/plant_table.dbf',
                'market_disc_rate': 7}

        timber.execute(args)

        #Delete all the generated files and directory
        if os.path.isdir('../../test_data/timber/Output/'):
            textFileList = os.listdir('../../test_data/timber/Output/')
            for file in textFileList:
                os.remove('../../test_data/timber/Output/' + file)
            os.rmdir('../../test_data/timber/Output/')

suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestTimberCore)
unittest.TextTestRunner(verbosity=2).run(suite)
