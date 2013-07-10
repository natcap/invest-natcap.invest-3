import os
import sys
import unittest

from invest_natcap.timber import timber
import invest_test_core

class TestInvestTimberCore(unittest.TestCase):
    def test_timber_model(self):
        data_dir = './invest-data/test/data/timber'
        output_dir = './test_out/timber'
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        
        args = {}
        args['workspace_dir'] = output_dir
        args['timber_shape_uri'] = os.path.join(
                data_dir, 'input/plantation.shp')
        args['attr_table_uri'] = os.path.join(
                data_dir, 'input/plant_table.dbf')   
        args['market_disc_rate'] = 7 

        timber.execute(args)

        out_uri = os.path.join(output_dir, 'Output/timber.shp')
        regression_uri = os.path.join(data_dir, 'regression_data/timber.shp')

        invest_test_core.assertTwoShapesEqualURI(
                self, regression_uri, out_uri)        
