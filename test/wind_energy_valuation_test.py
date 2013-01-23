"""URI level tests for the wind_energy valuation module"""

import os.path
import sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_valuation
import invest_test_core

class TestWindEnergyValuation(unittest.TestCase):
    def test_wind_energy_valuation_clip_and_project_datasource(self):
        """Regression test for clipping a shapefile from another shapefile and
            then projecting it to that shapefile"""
        #raise SkipTest

        regression_dir = \
              './data/wind_energy_regression_data/valuation/'
        input_dir = './data/wind_energy_data/'

        original_shape_uri = os.path.join(
                input_dir, 'testing_land.shp')

        aoi = ogr.Open(os.path.join(input_dir, 'testing_aoi_proj.shp'))

        regression_proj_uri = os.path.join(
                regression_dir, 'val_land_poly_projected.shp')
        regression_clip_uri = os.path.join(
                regression_dir, 'val_land_poly_clipped.shp')
        regression_aoi_uri = os.path.join(
                regression_dir, 'val_aoi_proj_to_land_poly.shp')
        
        reg_file_list = [
                regression_proj_uri, regression_clip_uri, regression_aoi_uri]

        output_dir = './data/test_out/wind_energy/valuation/clip_project/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_clipped_uri = os.path.join(output_dir, 'clipped.shp')
        out_projected_uri = os.path.join(output_dir, 'projected.shp')
        out_aoi_proj_uri = os.path.join(output_dir, 'aoi_to_land.shp')
       
        out_file_list = [out_projected_uri, out_clipped_uri, out_aoi_proj_uri]

        for out_uri in out_file_list:
            if os.path.isfile(out_uri):
                os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_valuation.clip_and_project_datasource(
            original_shape, aoi, out_clipped_uri, out_projected_uri,
            out_aoi_proj_uri)
        
        result_shape = None
        original_shape = None
        aoi = None

        for reg_uri, out_uri in zip(reg_file_list, out_file_list):
            invest_test_core.assertTwoShapesEqualURI(self, reg_uri, out_uri)


    def test_wind_energy_valuation_dictionary_to_shapefile(self):
        """A regression test for making a shapefile from a dictionary"""

        #raise SkipTest

        regression_dir = './data/wind_energy_regression_data/valuation/'

        expected_uri = os.path.join(regression_dir, 'dict_to_shape.shp')

        out_dir = './data/test_out/wind_energy/valuation/dict_to_shape/'

        out_uri = os.path.join(out_dir, 'dict_to_shape.shp')

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if os.path.isfile(out_uri):
            os.remove(out_uri)

        expected_dict = {}

        expected_dict[1] = {'lati':97, 'long':43, 'type':'grid'}
        expected_dict[2] = {'lati':96, 'long':44, 'type':'land'}

        result = wind_energy_valuation.dictionary_to_shapefile(
                expected_dict, 'tester', out_uri)

        result = None

        #invest_test_core.assertTwoShapesEqualURI(
        #self, expected_uri, out_uri)
