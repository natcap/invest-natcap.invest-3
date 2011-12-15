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
import numpy as np


class TestWaveEnergy(unittest.TestCase):

    def test_waveEnergy_clipShape(self):
        """A trivial test case that makes sure clipShape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""
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
        
        shapeToClip = ogr.Open(shapeToClipPath.encode(filesystemencoding))
        bindingShape = ogr.Open(bindingShapePath.encode(filesystemencoding))
        
        newShape = waveEnergy_core.clipShape(shapeToClip, bindingShape, newShapePath)
        
        layerCount = shapeToClip.GetLayerCount()
        layerCountNew = newShape.GetLayerCount()        
        self.assertEqual(layerCount, layerCountNew, 'The shapes DO NOT have the same number of layers')
        
        for layerNum in range(layerCount):
            layer = shapeToClip.GetLayer(layerNum)
            layerNew = newShape.GetLayer(layerNum)
            
            featCount = layer.GetFeatureCount()
            featCountNew = layerNew.GetFeatureCount()
            self.assertEqual(featCount, featCountNew, 'The layers DO NOT have the same number of features')
            
            feat = layer.GetNextFeature()
            featNew = layerNew.GetNextFeature()
            while feat is not None:
                layerDef = layer.GetLayerDefn()
                layerDefNew = layerNew.GetLayerDefn()
            
                fieldCount = layerDef.GetFieldCount()
                fieldCountNew = layerDefNew.GetFieldCount()
                self.assertEqual(fieldCount, fieldCountNew, 'The shapes DO NOT have the same number of fields')
                                            
                for fld_index in range(fieldCount):
                    field = feat.GetField(fld_index)
                    fieldNew = featNew.GetField(fld_index)
                    self.assertEqual(field, fieldNew, 'The field values DO NOT match')
                    
                feat.Destroy()
                featNew.Destroy()
                feat = layer.GetNextFeature()
                featNew = layerNew.GetNextFeature()
                
        newShape.Destroy()
        shapeToClip.Destroy()      
        bindingShape.Destroy()
        
#        if os.path.isdir(output_dir):
#            textFileList = os.listdir(output_dir)
#            for file in textFileList:
#                os.remove(output_dir + file)
#            os.rmdir(output_dir)
            
    def test_waveEnergy_clipShapeZero(self):
        """A trivial test case that makes sure clipShape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        testDir = '../../../test_data/wave_Energy'
        shapeToClipPath = testDir + os.sep + 'test_input/pointShapeTest.shp'
        bindingShapePath = testDir + os.sep + 'samp_input/AOI_WCVI.shp'
        newShapePath = testDir + os.sep + 'test_output/waveEnergy_NoClip.shp'
        
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        
        shapeToClip = ogr.Open(shapeToClipPath.encode(filesystemencoding))
        bindingShape = ogr.Open(bindingShapePath.encode(filesystemencoding))
        
        newShape = waveEnergy_core.clipShape(shapeToClip, bindingShape, newShapePath)
        
        layer = newShape.GetLayer(0)
        
        self.assertEqual(layer.GetFeatureCount(), 0)
        
        layer = None
        newShape.Destroy()
        shapeToClip.Destroy()
        bindingShape.Destroy()
        
    def test_waveEnergy_clipShapeProj(self):
        """A non trivial test case that makes sure clipShape returns the proper shape
        after it has been clipped by a polygon shapefile."""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        testDir = '../../../test_data/wave_Energy'
        shapeToClipPath = testDir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        bindingShapePath = testDir + os.sep + 'test_input/threePointShape.shp'
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
        
#        pointOneFields = [6025, 'Point', 572, 490, -126.933144, 47.600162, 2.8, 11.1]
#        pointTwoFields = [6064, 'Point', 573, 490, -126.866477, 47.600162, 2.8, 11.11]
#        pointThreeFields = [6101, 'Point', 574, 490, -126.79981, 47.600162, 2.79, 11.11]
        #It seems that the fields "FID" and "Shape" are not included for some reason when
        #Looping through all the fields of the shapefile
        pointOneFields = [572, 490, -126.933144, 47.600162, 2.8, 11.1]
        pointTwoFields = [573, 490, -126.866477, 47.600162, 2.8, 11.11]
        pointThreeFields = [574, 490, -126.79981, 47.600162, 2.79, 11.11]
        pointFieldArray = [pointOneFields, pointTwoFields, pointThreeFields]
        
        layer = newShape.GetLayer(0)
        featCountCalc = 3
        featCount = layer.GetFeatureCount()
        self.assertEqual(featCountCalc, featCount, 'The number of features are not correct')
        
        feat = layer.GetNextFeature()
        pointArrayIderator = 0
        while feat is not None:
            layerDef = layer.GetLayerDefn()
            pointField = pointFieldArray[pointArrayIderator]
            fieldCount = layerDef.GetFieldCount()
            fldCountCalc = 6
            self.assertEqual(fieldCount, fldCountCalc, 'The number of fields are not correct')
            for fld_index in range(fieldCount):
                field = feat.GetField(fld_index)
                fieldCalc = pointField[fld_index]
                self.assertEqual(field, fieldCalc, 'The field values do not match'+str(field)+'!='+str(fieldCalc))
                
            feat.Destroy()
            feat = layer.GetNextFeature()
            pointArrayIderator = pointArrayIderator+1
            
        newShape.Destroy()
        shapeToClip.Destroy()
        bindingShape.Destroy()

#    def test_waveEnergy_shapeToDict(self):
#        """Test pointShapeToDict to make sure that it works properly for different geometries"""
#        #This ensures we are not in Arc's python directory so that when
#        #we import gdal stuff we don't get the wrong GDAL version.
#        os.chdir(os.path.dirname(os.path.realpath(__file__)))
#        filesystemencoding = sys.getfilesystemencoding()
#        
#        
#        testDir = '../../../test_data/wave_Energy'
#        shapePath = testDir + os.sep + 'test_input/pointShapeTest.shp'
#        
#        #Add the Output directory onto the given workspace
#        output_dir = testDir + os.sep + 'test_output/'
#        if not os.path.isdir(output_dir):
#            os.mkdir(output_dir)
##        elif os.path.isfile(output_dir + 'timber.shp'):
##            os.remove(output_dir + 'timber.shp')
#
#        shapeToClip = ogr.Open(shapePath.encode(filesystemencoding))
#        key = ['LONG', 'LATI']
#        valueArray = ['LONG', 'LATI', 'HSAVG_M', 'TPAVG_S']
#        value = 'HSAVG_M'
#        xrange = [-126.933144, -126.866477, -126.79981]
#        yrange = [47.600162]
#        matrix = [[2.8, 2.8, 2.79]]
#        shapeArray = waveEnergy_core.pointShapeToDict(shapeToClip, key, valueArray, value)
#        self.assertEqual(len(xrange), len(shapeArray[0]), 'xranges do not have same number of elements')
#        self.assertEqual(len(yrange), len(shapeArray[1]), 'yranges do not have same number of elements')
#        self.assertEqual(len(matrix), len(shapeArray[2]), 'matrices do not have same number of elements')
#        shapeMatrix = shapeArray[2]
#        for index, var in enumerate(matrix):
#            for innerIndex, num in enumerate(var):
#                self.assertEqual(num, shapeMatrix[index][innerIndex], 'The values of the matrices do not match')
#        
#        shapeToClip.Destroy()
        
    def test_waveEnergy_getPointsValues(self):
        """Test getPointsValues to make sure that it works properly for different geometries"""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        
        testDir = '../../../test_data/wave_Energy'
        shapePath = testDir + os.sep + 'test_input/pointShapeTest.shp'
        
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')

        shapeToClip = ogr.Open(shapePath.encode(filesystemencoding))
        key = ['LONG', 'LATI']
        valueArray = ['LONG', 'LATI', 'HSAVG_M', 'TPAVG_S']
        value = 'HSAVG_M'
        points = [[-126.933144, 47.600162], [-126.866477, 47.600162], [-126.79981, 47.600162]]
        values = [2.8, 2.8, 2.79]
        shapeArray = waveEnergy_core.getPointsValues(shapeToClip, key, valueArray, value)
        self.assertEqual(len(points), len(shapeArray[0]), 'The number of points do not match')
        self.assertEqual(len(values), len(shapeArray[1]), 'The number of values do not match')
        shapePoints = shapeArray[0]
        shapeValues = shapeArray[1]
        calcDict = {}
        funDict = {}
        for index, var in enumerate(points):
            calcDict[tuple(var)] = values[index]
        for index, var in enumerate(shapePoints):
            funDict[tuple(var)] = shapeValues[index]
        for key, val in calcDict.iteritems():
            if key in funDict:
                self.assertEqual(val, funDict[key], 'The values do not match')
            else:
                self.assertEqual(0, 1, 'The keys do not match')
            
        shapeToClip.Destroy()
        
    def test_waveEnergy_capturedWaveEnergyToShape(self):
        """Test capturedWaveEnergyToShape to make sure that it works properly for different geometries"""
        #This ensures we are not in Arc's python directory so that when
        #we import gdal stuff we don't get the wrong GDAL version.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        filesystemencoding = sys.getfilesystemencoding()
        
        
        testDir = '../../../test_data/wave_Energy'
        shapePath = testDir + os.sep + 'test_input/pointShapeTest.shp'
        newPath = str(testDir + os.sep + 'test_output/pointShapeSum.shp')
        waveShape = ogr.Open(shapePath.encode(filesystemencoding), 1)
        
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')

        waveShapeCopy = ogr.GetDriverByName('Memory').CopyDataSource(waveShape, '')
#        waveShapeCopy.Destroy()
#        waveShapeCopy = ogr.Open(newPath.encode(filesystemencoding), 1)
        
        testDict = {(572, 490):2302, (573, 490):1453, (574, 490):2103}
        ijArray = [[572, 490], [573, 490], [574, 490]]
        waveEnergy_core.capturedWaveEnergyToShape(testDict, waveShapeCopy)
        
        layer = waveShapeCopy.GetLayer(0)
        #Need to reset the layer because the function call goes through the features in
        #the layer and does not reset or close.
        layer.ResetReading()
        feat = layer.GetNextFeature()
        compDict = {}
        while feat is not None:
            tempArray = []
            for fld in ('I', 'J', 'capWE_Sum'):
                index = feat.GetFieldIndex(fld)
                fieldVal = feat.GetField(index)
                tempArray.append(fieldVal)
            compDict[(tempArray[0], tempArray[1])] = tempArray[2]

            feat.Destroy()
            feat = layer.GetNextFeature()
            
        self.assertEqual(len(testDict), len(compDict), 'The lengths of the dictionaries are not the same')
            
        for key, val in testDict.iteritems():
            if key in compDict:
                self.assertEqual(val, compDict[key], 'The values corresponding to the keys do not match'+str(val)+':'+str(compDict[key]))
            else:
                self.assertEqual(0, 1, 'The key does not exist in the new feature')
                
            
        waveShape.Destroy()
        waveShapeCopy.Destroy()
        
        
    def test_waveEnergy_computeWaveEnergyCapacity(self):
        """Test computWaveEnergyCapacity function to make sure it works properly"""
               
#        waveData = 'A dictionary with key (I,J) and value 2D array'
        waveData = {0:[1,2,3,4,5], 1:[1,2,3,4],
                    (520, 490):[[0, 10, 13, 9, 7],
                                [8, 15, 17, 13, 3],
                                [0, 3, 11, 9, 7],
                                [11, 17, 23, 19, 12]],
                    (521, 491):[[-1, 6.5, 13.3, 9, 7],
                                [-8, -5, 170, 13, 0],
                                [2, 3, 11.5, 9, 7.25],
                                [11, 17, 23, 19, 12]]
                    }
#        interpZ = 'An interpolated object from machine performace and waveData ranges'
        interpZ = [[0, 0, 1, 3, 8],[0, 3, 5, 9, 7],[1, 4, 5, 3, 0],[0, 0, 0, 0, 0]]
#        machineParam = 'A dictionary with CapMax TpMax and HsMax'
        machineParam = {'CapMax':{'VALUE':20}, 'TpMax':{'VALUE':4}, 'HsMax':{'VALUE':3}}
        result = {(520, 490):0.0762, (521, 491):0.22116}
        
        weSum = waveEnergy_core.computeWaveEnergyCapacity(waveData, interpZ, machineParam)
               
        """Loop that compares dictionaries weSum and result checking key, sum values"""
        for key in result:
            if key in weSum:
                self.assertAlmostEqual(result[key], weSum[key], 8, 'The values do not match for key '+str(weSum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')
        
    def test_waveEnergy_waveEnergyInterp(self):
        waveData = {0:[1,2,3,4,5,6,7,8], 1:[.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]}
        machinePerf = [[2,3,4,7], [1, 2, 3], 
                       [0, 8, 20, 10], 
                       [6, 18, 23, 13], 
                       [0, 8, 20, 0]]
        result = [[0, 0, 8, 20, 16.6666667, 13.33333, 10, 10],
                  [0, 0, 8, 20, 16.66666667, 13.33333333, 10, 10],
                  [3, 3, 13, 21.5, 18.16666667, 14.83333333, 11.5, 11.5],
                  [6, 6, 18, 23, 19.66666667, 16.33333333, 13, 13],
                  [3, 3, 13, 21.5, 16.5, 11.5, 6.5, 6.5],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0]]
        result = np.array(result)
        interpZ = waveEnergy_core.waveEnergyInterp(waveData, machinePerf)
        
        self.assertEqual(result.shape, interpZ.shape, 'The shapes are not the same')
        
        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, interpZ[indexOut][indexIn], 5, 'Values do not match')
        
        
def waveEnergyInterp(waveData, machinePerf):
    x = np.array(machinePerf.pop(0), dtype='f')
    y = np.array(machinePerf.pop(0), dtype='f')
    z = np.array(machinePerf, dtype='f')
    newx = waveData[0]
    newy = waveData[1]
    interpZ = invest_cython_core.interpolateMatrix(x, y, z, newx, newy)
    return interpZ
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

