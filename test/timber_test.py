import os
import sys
import unittest

from invest_natcap.timber import timber

#Create a variable to prepend to each path
current_folder = os.path.dirname(os.path.abspath(__file__)) + os.sep

class TestInvestTimberCore(unittest.TestCase):
    def test_timber_model(self):
        args = {'output_dir': current_folder + 'data/timber',
                'timber_shape_uri': current_folder +
                    'data/timber/input/plantation.shp',
                'attr_table_uri': current_folder +
                    'data/timber/input/plant_table.dbf',
                'market_disc_rate': 7}

        timber.execute(args)

        #Delete all the generated files and directory
        if os.path.isdir(current_folder + 'data/timber/Output/'):
            textFileList = os.listdir(current_folder + 'data/timber/Output/')
            for file in textFileList:
                os.remove(current_folder + 'data/timber/Output/' + file)
            os.rmdir(current_folder + 'data/timber/Output/')
