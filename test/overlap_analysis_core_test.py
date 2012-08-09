'''Testing framework specifically for the overlap analysis core. This will test
the individual functions of the core, as well as running a comprehensive test for the
entire class.
'''

import os
import unittest

import invest_test_core

from invest_natcap.overlap_analysis import overlap_analysis_core
from invest_natcap.overlap_analysis import overlap_analysis
from osgeo import ogr

class TestOverlapAnalysisCore(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace'] = './data/test_out/Overlap'
        args['intermediate'] = os.path.join(args['workspace'], 'Intermediate')

        if not os.path.isdir(args['intermediate']):
            os.makedirs(args['intermediate'])
            
        args['do_grid'] = True
        args['grid_size'] = 1000

        self.args = args
        
    def test_reg_overall(self):
        
        self.args['zone_layer_file'] = ogr.Open('./data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = True
        self.args['do_intra'] = True

        files_loc = './data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_analysis.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
         inter_table_loc = './data/test_out/Overlap/Input/inter_activ_table.csv'
        inter_table = overlap_analysis.format_over_table(inter_table_loc)
        self.args['over_layer_dict'] = inter_table

        overlap_analysis_core.execute(self.args)

        #Now, using the workspace folder that we have selected, need to retrieve it and compare
        #the two output files against hand-calculated rasters? Or somehow make raster myself.
        
        #In the meantime, get the created files.
        output_dir = os.path.join(self.args['workspace'], 'Output')
        unweighted_output = os.path.join(output_dir, 'hu_freq.tif')
        weighted_output = os.path.join(output_dir, 'hu_impscore.tif')


