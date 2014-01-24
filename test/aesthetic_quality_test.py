import unittest
import os
import gdal
from invest_natcap.aesthetic_quality import aesthetic_quality


class AestheticQualityTest(unittest.TestCase):
    """Test class for test functions of the AQ model"""

##    def test_smoke(self):
##        """Smoke test for aq"""
##
##        args = {}
##        args['workspace_dir'] = 'data/test_out/aq_test'
##        if not os.path.isdir(args['workspace_dir']):
##            os.makedirs(args['workspace_dir'])
##
##        args['aoi_uri'] = 'data/aesthetic_quality/AOI_WCVI.shp'
##        args['structure_uri'] = 'data/aesthetic_quality/AquaWEM_points.shp'
##        args['dem_uri'] = 'data/wave_energy_data/samp_input/global_dem'
##        args['refraction'] = 0.13
##        args['cellSize'] = 30
##        args['pop_uri'] = 'data/aesthetic_quality/aoi_pop.tif'
##        args['overlap_uri'] = 'data/aesthetic_quality/BC_parks.shp'
##        aesthetic_quality.execute(args)

#    def test_reclassify_quantile_dataset_uri(self):
#        dataset_uri = "/home/mlacayo/Desktop/aq_tif/vshed.tif"
#        quantile_list = [25, 50, 75, 100]
#        dataset_out_uri = "/home/mlacayo/Desktop/vshed_qual.tif"
#        datatype_out = gdal.GDT_Int32
#        nodata_out = -1
        
#        aesthetic_quality.reclassify_quantile_dataset_uri(dataset_uri,
#                                                          quantile_list,
#                                                          dataset_out_uri,
#                                                          datatype_out,
#                                                          nodata_out)

