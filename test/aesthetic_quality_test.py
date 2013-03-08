import unittest
import os

from invest_natcap.aesthetic_quality import aesthetic_quality


class AestheticQualityTest(unittest.TestCase):
    """Test class for test functions of the AQ model"""

    def test_smoke(self):
        """Smoke test for aq"""

        args = {}
        args['workspace_dir'] = 'data/test_out/aq_test'
        if not os.path.isdir(args['workspace_dir']):
            os.makedirs(args['workspace_dir'])

        args['aoi_uri'] = 'data/aesthetic_quality/AOI_WCVI.shp'
        args['structure_uri'] = 'data/aesthetic_quality/AquaWEM_points.shp'
        args['dem_uri'] = 'data/wave_energy_data/samp_input/global_dem'
        args['refraction'] = 0.13
        args['cellSize'] = 30
        args['pop_uri'] = 'data/aesthetic_quality/aoi_pop.tif'
        args['overlap_uri'] = 'data/aesthetic_quality/BC_parks.shp'
        aesthetic_quality.execute(args)
