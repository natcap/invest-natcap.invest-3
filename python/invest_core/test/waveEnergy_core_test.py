import sys, os

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
os.chdir(cmd_folder)

import unittest
import waveEnergy_core
import math
from dbfpy import dbf
from osgeo import ogr


class TestWaveEnergy(unittest.TestCase):

    def test_waveEnergy_clipShape(self):
        """Test clipShape to make sure that it works properly for different geometries"""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        testDir = '../../../test_data/wave_Energy'
        shapeToClipPath = testDir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        bindingShapePath = testDir + os.sep + 'samp_input/WaveData/WCNA_extract.shp'
        newShapePath = testDir + os.sep + 'test_output/waveEnergy_Clipz.shp'
        
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')
        
        shapeToClip = ogr.Open(shapeToClipPath.encode(filesystemencoding))
        bindingShape = ogr.Open(bindingShapePath.encode(filesystemencoding))
        
        newShape = waveEnergy_core.clipShape(shapeToClip, bindingShape, newShapePath)

    def test_waveEnergy_clipShapeProj(self):
        """Test clipShape to make sure that it works properly for different geometries"""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        testDir = '../../../test_data/wave_Energy'
        shapeToClipPath = testDir + os.sep + 'samp_input/WaveData/WCNA_extract.shp'
        bindingShapePath = testDir + os.sep + 'samp_input/AOI_WCVI.shp'
        newShapePath = testDir + os.sep + 'test_output/waveEnergy_ClipAOI.shp'
        
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')
        
        shapeToClip = ogr.Open(shapeToClipPath.encode(filesystemencoding))
        bindingShape = ogr.Open(bindingShapePath.encode(filesystemencoding))
        
        newShape = waveEnergy_core.clipShape(shapeToClip, bindingShape, newShapePath)


#    def test_waveEnergy_with_inputs(self):
#        """Test timber model with real inputs.  Compare copied and modified shapefile with valid
#            shapefile that was created from the same inputs.  Regression test."""
#        #Open table and shapefile
#        attr_table = dbf.Dbf('../../../timber/input/plant_table.dbf')
#        test_shape = ogr.Open('../../../timber/input/plantation.shp', 1)
#
#        #Add the Output directory onto the given workspace
#        output_dir = '../../../test_data/timber' + os.sep + 'Output/'
#        if not os.path.isdir(output_dir):
#            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')
#
#        shape_source = output_dir + 'timber.shp'
#
#        ogr.GetDriverByName('ESRI Shapefile').\
#            CopyDataSource(test_shape, shape_source)
#
#        timber_output_shape = ogr.Open('../../../test_data/timber/Output/timber.shp', 1)
#        timber_output_layer = timber_output_shape.GetLayerByName('timber')
#
#        args = {'timber_shape': timber_output_shape,
#               'attr_table':attr_table,
#               'mdr':7,
#               }
#
#        timber_core.execute(args)
#
#        valid_output_shape = ogr.Open('../../../timber/sample_output/timber.shp')
#        valid_output_layer = valid_output_shape.GetLayerByName('timber')
#        #Check that the number of features (polygons) are the same between shapefiles
#        num_features_valid = valid_output_layer.GetFeatureCount()
#        num_features_copy = timber_output_layer.GetFeatureCount()
#        self.assertEqual(num_features_valid, num_features_copy)
#        #If number of features are equal, compare each shapefiles 3 fields
#        if num_features_valid == num_features_copy:
#            for i in range(num_features_valid):
#                feat = valid_output_layer.GetFeature(i)
#                feat2 = timber_output_layer.GetFeature(i)
#                for field in ('TNPV', 'TBiomass', 'TVolume'):
#                    field_index = feat.GetFieldIndex(field)
#                    field_value = feat.GetField(field_index)
#                    field_index2 = feat2.GetFieldIndex(field)
#                    field_value2 = feat2.GetField(field_index2)
#                    self.assertAlmostEqual(field_value, field_value2, 2)
#        #This is how OGR cleans up and flushes datasources
#        test_shape.Destroy()
#        timber_output_shape.Destroy()
#        valid_output_shape = None
#        timber_output_shape = None
#        test_shape = None
#        timber_output_layer = None
#        attr_table.close()
#        #Delete all the generated files and directory
#        if os.path.isdir('../../../test_data/timber/Output/'):
#            textFileList = os.listdir('../../../test_data/timber/Output/')
#            for file in textFileList:
#                os.remove('../../../test_data/timber/Output/' + file)
#            os.rmdir('../../../test_data/timber/Output/')

suite = unittest.TestLoader().loadTestsFromTestCase(TestWaveEnergy)
unittest.TextTestRunner(verbosity=2).run(suite)

