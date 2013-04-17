import unittest
import os

from invest_natcap.flood_mitigation import flood_mitigation

TEST_DATA = os.path.join('data', 'flood_mitigation')
SAMP_INPUT = os.path.join(TEST_DATA, 'samp_input')

class FloodMitigationTest(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.join(TEST_DATA, 'test_workspace')
        self.curve_numbers = os.path.join(SAMP_INPUT, 'curve_numbers.tif')

        try:
            os.makedirs(self.workspace)
        except OSError:
            # If folder already exists.
            pass

    def test_cn_dry_adjustment(self):
        dry_season_cn = os.path.join(self.workspace, 'dry_season_cn.tif')
        flood_mitigation.adjust_cn_for_dry_season(self.curve_numbers,
            dry_season_cn)

