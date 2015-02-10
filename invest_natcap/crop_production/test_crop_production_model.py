import unittest
import os
import pprint

from numpy import testing
import numpy as np

import crop_production_model

workspace_dir = '../../test/invest-data/Crop_Production'
input_dir = '../../test/invest-data/Crop_Production/input'
pp = pprint.PrettyPrinter(indent=4)


class TestModelFuntion1(unittest.TestCase):
    def setUp(self):
        self.args = {

        }

    def test_run1(self):
        guess = crop_production.execute(self.args, create_outputs=False)
        pass

    def test_run2(self):
        guess = crop_production.execute(self.args, create_outputs=False)
        pass


class TestModelFuntion2(unittest.TestCase):
    def setUp(self):
        self.args = {

        }

    def test_run1(self):
        guess = crop_production.execute(self.args, create_outputs=False)
        pass

    def test_run2(self):
        guess = crop_production.execute(self.args, create_outputs=False)
        pass


if __name__ == '__main__':
    unittest.main()
