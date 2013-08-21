import unittest
import logging

from invest_natcap.aesthetic_quality import aesthetic_quality_core

class TestAestheticQualityCore(unittest.TestCase):
    def SetUp(self):
        pass

    def test_extreme_cell_angles(self):
        array_shape = (3, 3)
        viewpoint = (1, 1)
        aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)

    def test_viewshed(self):
        pass

    def tare_down(self):
        pass
