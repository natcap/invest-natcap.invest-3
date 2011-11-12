"""URI level tests for the carbon biophysical module"""

import os, sys
import unittest
import invest_test_core

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import sediment_biophysical

class TestSedimentBiophysical(unittest.TestCase):
    def test_sediment_biophysical_regression(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = '../../../sediment_biophysical_output'
        baseDir = '../../../sediment_test_data'
        args['dem_uri'] = '%s/dem' % baseDir
        args['erosivity_uri'] = '%s/erosivity' % baseDir
        args['erodibility_uri'] = '%s/erodibility.tif' % baseDir
        args['landuse_uri'] = '%s/landuse_90.tif' % baseDir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % baseDir
        args['subwatersheds_uri'] = '%s/subwatersheds.shp' % baseDir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % baseDir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % baseDir

        #table
        args['biophysical_table_uri'] = '%s/' % baseDir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        sediment_biophysical.execute(args)

        #Regression tests go here
#        #assert that '../../test_data/tot_C_cur.tif' equals
#        #../../carbon_output/Output/tot_C_cur.tif
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/tot_C_cur.tif",
#            '../../test_data/tot_C_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/tot_C_fut.tif",
#            '../../test_data/tot_C_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/sequest.tif",
#            '../../test_data/sequest_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/bio_hwp_cur.tif",
#            '../../test_data/bio_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/bio_hwp_fut.tif",
#            '../../test_data/bio_hwp_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/c_hwp_cur.tif",
#            '../../test_data/c_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/c_hwp_fut.tif",
#            '../../test_data/c_hwp_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/vol_hwp_cur.tif",
#            '../../test_data/vol_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/vol_hwp_fut.tif",
#            '../../test_data/vol_hwp_fut_regression.tif')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSedimentBiophysical)
    unittest.TextTestRunner(verbosity=2).run(suite)
