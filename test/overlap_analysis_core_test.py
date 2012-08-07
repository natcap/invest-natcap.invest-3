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
        
	def test_reg_overall:
		
		self.args['zone_layer_file'] = ogr.Open('./data/test_out/Overlap/Input/test_aoi.shp')
		self.args['do_inter'] = True
		self.args['do_intra'] = True

		files_loc = './data/test_out/Overlap/Input/Test_Activity'

		files_dict = overlap_analysis.get_files_dict(files_loc)

		args['overlap_files'] = files_dict
	 
	 	inter_table_loc = './data/test_out/Overlap/Input/inter_activ_table.csv'
		inter_table = overlap_analysis.format_over_table(inter_table_loc)
		args['over_layer_dict'] = inter_table
