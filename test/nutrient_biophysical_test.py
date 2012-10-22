import unittest

class NutrientBiophysicalTest(unittest.TestCase):
    """Test class for test functions of the Nutrient retention model
    (biophysical component)."""
    def setUp(self):
        self.args = {
            'workspace_uri': '',
            'dem_uri': '',
            'pixel_yield_uri': '',
            'landuse_uri': '',
            'watersheds_uri': '',
            'subwatersheds_uri': '',
            'bio_table_uri': '',
            'threshold_table_uri': '',
            'nutrient_type': '',
            'accum_threshold': 0
        }_

    def test_smoke(self):
        """Smoke test for nutrient retention: biophysical"""
        pass

