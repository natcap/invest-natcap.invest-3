import os, sys

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import unittest
import timber

class TestInvestTimberCore(unittest.TestCase):
    def test_timber_model(self):
        args = {'output_dir': '../../test_data/timber',
                'timber_shape_uri': '../../test_data/timber/input/plantation.shp',
                'attr_table_uri': '../../test_data/timber/input/plant_table.dbf',
                'market_disc_rate': 7}

        timber.execute(args)

        #Delete all the generated files and directory
        if os.path.isdir('../../test_data/timber/Output/'):
            textFileList = os.listdir('../../test_data/timber/Output/')
            for file in textFileList:
                os.remove('../../test_data/timber/Output/' + file)
            os.rmdir('../../test_data/timber/Output/')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestTimberCore)
    unittest.TextTestRunner(verbosity=2).run(suite)
