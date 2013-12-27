'''Testing framework specifically for the overlap analysis core. This will test
the individual functions of the core, as well as running a comprehensive test for the
entire class.
'''

import os
import unittest
import logging

import invest_test_core

from invest_natcap.overlap_analysis import overlap_core
from invest_natcap.overlap_analysis import overlap_analysis

from osgeo import ogr

LOGGER = logging.getLogger('overlap_analysis_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestOverlapAnalysisCore(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/Overlap'
        args['intermediate'] = os.path.join(args['workspace_dir'], 'Intermediate')
        args['output'] = os.path.join(args['workspace_dir'], 'Ouput')

        if not os.path.isdir(args['intermediate']):
            os.makedirs(args['intermediate'])
        if not os.path.isdir(args['output']):
            os.makedirs(args['output'])

        args['do_grid'] = True
        args['grid_size'] = 500 

        self.args = args
        
    def test_all_on(self):
        
        self.args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = True
        self.args['do_intra'] = True
        self.args['intra_name'] = 'RI'    
        self.args['do_hubs'] = True
        self.args['decay_amt'] = 0.0005
        self.args['hubs_uri'] = './invest-data/test/data/test_out/Overlap/Input/PopulatedPlaces_WCVI.shp'

        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_core.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
        inter_table_loc = './invest-data/test/data/test_out/Overlap/Input/inter_activ_table.csv'
        inter_table = overlap_analysis.format_over_table(inter_table_loc)
        self.args['over_layer_dict'] = inter_table

        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        overlap_analysis_core.execute(self.args)

    def test_no_weighted(self):

        self.args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = False 
        self.args['do_intra'] = False

        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_core.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        overlap_analysis_core.execute(self.args)

    def test_only_intra(self):

        self.args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = False 
        self.args['do_intra'] = True
        self.args['intra_name'] = 'RI'    

        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_core.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        overlap_analysis_core.execute(self.args)
       
    def test_only_inter(self):
        
        self.args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = True
        self.args['do_intra'] = False

        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_core.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
        inter_table_loc = './invest-data/test/data/test_out/Overlap/Input/inter_activ_table.csv'
        inter_table = overlap_analysis.format_over_table(inter_table_loc)
        self.args['over_layer_dict'] = inter_table

        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        overlap_analysis_core.execute(self.args)
    
    def test_only_hubs(self):

        self.args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_aoi.shp')
        self.args['do_inter'] = False 
        self.args['do_intra'] = False
        self.args['do_hubs'] = True
        self.args['decay_amt'] = 0.0005
        self.args['hubs_uri'] = './invest-data/test/data/test_out/Overlap/Input/PopulatedPlaces_WCVI.shp'
        
        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_core.get_files_dict(files_loc)

        self.args['overlap_files'] = files_dict
     
        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        overlap_analysis_core.execute(self.args)
