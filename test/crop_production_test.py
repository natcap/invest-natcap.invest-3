'''
python -m unittest test_crop_production
'''

import unittest
import os
import pprint

import crop_production_data  as test_data
import invest_natcap.crop_production.crop_production as crop_production

current_dir = os.path.dirname(os.path.realpath(__file__))
workspace_dir = os.path.join(
	current_dir, './invest-data/Crop_Production')
input_dir = os.path.join(
	current_dir, './invest-data/Crop_Production/input')
pp = pprint.PrettyPrinter(indent=4)


# class TestOverallModel1(unittest.TestCase):
#     def setUp(self):
#         self.args = test_data.get_large_dataset_args()

#     def test_run(self):
#         guess = crop_production.execute(self.args)


if __name__ == '__main__':
    unittest.main()
