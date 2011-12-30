import sys
import os
import unittest
import math
import csv

from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *
from invest_natcap.dbfpy import dbf
import numpy as np

from invest_natcap.wave_energy import waveEnergy_core
import waveEnergy_biophysical

class TestWaveEnergy(unittest.TestCase):

    def test_waveEnergy_biophysical(self):
        """Runs the biophysical part of the Wave Energy Model (WEM).
    
        args['wave_base_data'] - a dictionary of seastate bin data.
        args['analysis_area'] - a point geometry shapefile representing the relevant WW3 points
        args['analysis_area_extract'] - a polygon geometry shapefile encompassing the broader range
                                        of interest.
        args['AOI'] - a polygon geometry shapefile outlining a more specific area of interest.
        args['machine_perf'] - a 2D array representing the machine performance table.
        args['machine_param'] - a dictionary which holds the machine parameter values.
        args['dem'] - a GIS raster file of the global elevation model
        args['workspace_dir'] - the workspace path
        args['wave_data_dir'] - the wave data path, used for retreiving other relevant files.
            
        """
        testDir = './data/test_data/wave_Energy'
        analysisPath = testDir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        analysisExtractPath = testDir + os.sep + 'samp_input/WaveData/WCNA_extract.shp'
        aoiPath = testDir + os.sep + 'samp_input/AOI_WCVI.shp'
        demPath = testDir + os.sep + 'samp_input/global_dem'
        waveFilePath = testDir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.txt'
        machinePerfPath = './data/test_data/wave_Energy/samp_input/Machine_PelamisPerfCSV.csv'
        machineParamPath = './data/test_data/wave_Energy/samp_input/Machine_PelamisParamCSV.csv'
        #Set all arguments to be passed
        args = []
        args['wave_base_data'] = waveEnergy_biophysical.extrapolateWaveData(waveFilePath)
        args['analysis_area'] = ogr.Open(analysisPath, 1)
        args['analysis_area_extract'] = ogr.Open(analysisExtractPath)
        args['AOI'] = ogr.Open(aoiPath)
        args['dem'] = gdal.Open(demPath)
        args['workspace_dir'] = './data/test_data/wave_Energy'
        args['wave_data_dir'] = './data/test_data/wave_Energy/samp_input/WaveData'
        #Create a 2D array of the machine performance table and place the row
        #and column headers as the first two arrays in the list of arrays
        try:
            machine_perf_twoDArray = [[], []]
            machinePerfFile = open(machinePerfPath)
            reader = csv.reader(machinePerfFile)
            getRow = True
            for row in reader:
                if getRow:
                    machine_perf_twoDArray[0] = row[1:]
                    getRow = False
                else:
                    machine_perf_twoDArray[1].append(row.pop(0))
                    machine_perf_twoDArray.append(row)
            machinePerfFile.close()
            args['machine_perf'] = machine_perf_twoDArray
        except IOError, e:
            print 'File I/O error' + e

        #Create a dictionary whose keys are the 'NAMES' from the machine parameter table
        #and whose corresponding values are dictionaries whose keys are the column headers of
        #the machine parameter table with corresponding values
        try:
            machine_params = {}
            machineParamFile = open(machineParamPath)
            reader = csv.DictReader(machineParamFile)
            for row in reader:
                machine_params[row['NAME'].strip()] = row
            machineParamFile.close()
            args['machine_param'] = machine_params
        except IOError, e:
            print 'File I/O error' + e


        waveEnergy_core.biophysical(args)

        #Check that output/intermediate files have been made

        #Check that resulting rasters are correct

    def test_waveEnergy_changeProjection(self):
        testDir = './data/test_data/wave_Energy'
        shapeToReprojectPath = testDir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        projection = testDir + os.sep + 'test_input/WGS_1984_UTM_Zone_10N.prj'
        outputPath = testDir + os.sep + 'test_output/waveEnergy_Clip_prj.shp'

        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shapeToReproject = ogr.Open(shapeToReprojectPath)

        waveEnergy_core.changeProjection(shapeToReproject, projection, outputPath)


    def test_waveEnergy_clipShape(self):
        """A trivial test case that makes sure clipShape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""
        filesystemencoding = sys.getfilesystemencoding()

        testDir = './data/test_data/wave_Energy'
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
        filesystemencoding = sys.getfilesystemencoding()

        testDir = './data/test_data/wave_Energy'
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
        filesystemencoding = sys.getfilesystemencoding()

        testDir = './data/test_data/wave_Energy'
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
                self.assertEqual(field, fieldCalc, 'The field values do not match' + str(field) + '!=' + str(fieldCalc))

            feat.Destroy()
            feat = layer.GetNextFeature()
            pointArrayIderator = pointArrayIderator + 1

        newShape.Destroy()
        shapeToClip.Destroy()
        bindingShape.Destroy()

#    def test_waveEnergy_shapeToDict(self):
#        """Test pointShapeToDict to make sure that it works properly for different geometries"""
#        filesystemencoding = sys.getfilesystemencoding()
#        
#        
#        testDir = './data/test_data/wave_Energy'
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
        filesystemencoding = sys.getfilesystemencoding()


        testDir = './data/test_data/wave_Energy'
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
        filesystemencoding = sys.getfilesystemencoding()


        testDir = './data/test_data/wave_Energy'
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
                self.assertEqual(val, compDict[key], 'The values corresponding to the keys do not match' + str(val) + ':' + str(compDict[key]))
            else:
                self.assertEqual(0, 1, 'The key does not exist in the new feature')


        waveShape.Destroy()
        waveShapeCopy.Destroy()


    def test_waveEnergy_computeWaveEnergyCapacity(self):
        """Test computWaveEnergyCapacity function to make sure it works properly"""

#        waveData = 'A dictionary with key (I,J) and value 2D array'
        waveData = {0:[1, 2, 3, 4, 5], 1:[1, 2, 3, 4],
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
        interpZ = [[0, 0, 1, 3, 8], [0, 3, 5, 9, 7], [1, 4, 5, 3, 0], [0, 0, 0, 0, 0]]
#        machineParam = 'A dictionary with CapMax TpMax and HsMax'
        machineParam = {'CapMax':{'VALUE':20}, 'TpMax':{'VALUE':4}, 'HsMax':{'VALUE':3}}
        result = {(520, 490):0.0762, (521, 491):0.22116}

        weSum = waveEnergy_core.computeWaveEnergyCapacity(waveData, interpZ, machineParam)

        """Loop that compares dictionaries weSum and result checking key, sum values"""
        for key in result:
            if key in weSum:
                self.assertAlmostEqual(result[key], weSum[key], 8, 'The values do not match for key ' + str(weSum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')

    def test_waveEnergy_waveEnergyInterp(self):
        waveData = {0:[1, 2, 3, 4, 5, 6, 7, 8], 1:[.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]}
        machinePerf = [[2, 3, 4, 7], [1, 2, 3],
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

    def test_waveEnergy_clipRasterFromPolygon(self):
        filesystemencoding = sys.getfilesystemencoding()

        testDir = './data/test_data/wave_Energy'
        shapePath = testDir + os.sep + 'test_input/threePointShape.shp'
        rasterPath = testDir + os.sep + 'test_input/noAOIWP.tif'
        path = testDir + os.sep + 'test_output/wpClipped.tif'

        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape = ogr.Open(shapePath)
        raster = gdal.Open(rasterPath)

        newRaster = waveEnergy_core.clipRasterFromPolygon(shape, raster, path)

        newBand = newRaster.GetRasterBand(1)
        band = raster.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        testMatrix = [36.742653, 36.675091, 36.606201, 36.537350, 36.469341,
                      36.814983, 36.763050, 36.704857, 36.646111, 36.587391]
        matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
        newMatrix = newBand.ReadAsArray(0, 0, newBand.XSize, newBand.YSize)
        tempMatrix = []
        for index, item in enumerate(newMatrix):
            for i, val in enumerate(item):
                if val != nodata:
                    tempMatrix.append(val)
                    self.assertEqual(val, matrix[index][i], 'Values are not the same')

        self.assertEqual(len(tempMatrix), 10, 'Number of pixels do not match')

        for i, val in enumerate(testMatrix):
            self.assertAlmostEqual(val, tempMatrix[i], 4)

        newRaster = None

    def test_waveEnergy_interpPointsOverRaster(self):
        testDir = './data/test_data/wave_Energy'
        path = testDir + os.sep + 'test_output/fourbyfourRaster.tif'
        #Create a blank raster of small dimensions.
        driver = gdal.GetDriverByName('GTIFF')
        raster = driver.Create(path, 4, 4, 1, gdal.GDT_Float32)
        raster.SetGeoTransform([-129, 1, 0, 48, 0, -1])
        raster.GetRasterBand(1).SetNoDataValue(0)
        raster.GetRasterBand(1).Fill(0)
        #Hard code points and values
        points = np.array([[-128, 47], [-128, 45], [-126, 47], [-126, 45]])
        values = np.array([10, 12, 14, 16])
        #Hand Calculate what interpolated values should be and set as matrix
        result = np.array([[  0., 0., 0., 0.],
                           [  0., 10., 12., 14.],
                           [  0., 11., 13., 15.],
                           [  0., 12., 14., 16.]])

        waveEnergy_core.interpPointsOverRaster(points, values, raster)
        band = raster.GetRasterBand(1)
        matrix = band.ReadAsArray()
        self.assertEqual(matrix.size, result.size, 'The sizes are not the same')
        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, matrix[indexOut][indexIn], 5)


#    def interpPointsOverRaster(points, values, raster):
#    """Interpolates the values of a given set of points and values to the points
#    of a raster and writes the interpolated matrix to the raster band
#    
#    points - A 2D array of points, where the points are represented as [x,y]
#    values - A list of values corresponding to the points of 'points'
#    raster - A raster to write the interpolated values too
#    
#    returns - Nothing
#    """
#    #Set the points and values to numpy arrays
#    points = np.array(points)
#    values = np.array(values)
#    #Get the dimensions from the raster as well as the GeoTransform information
#    gt = raster.GetGeoTransform()
#    band = raster.GetRasterBand(1)
#    xsize = band.XSize
#    ysize = band.YSize
#    #newpoints = np.array([[x,y] for x in np.arange(gt[0], xsize*gt[1]+gt[0] , gt[1]) for y in np.arange(gt[3], ysize*gt[5]+gt[3], gt[5])])
#    #Make a numpy array representing the points of the raster (the points are the pixels)
#    newpoints = np.array([[gt[0]+gt[1]*i,gt[3]+gt[5]*j] for i in np.arange(xsize) for j in np.arange(ysize)])
#    #Interpolate the points and values from the shapefile from earlier
#    spl = ip(points, values, fill_value=0)
#    #Run the interpolator object over the new set of points from the raster. Will return a list of values.
#    spl = spl(newpoints)
#    #Reshape the list of values to the dimensions of the raster for writing.
#    #Transpose the matrix provided from 'reshape' because gdal thinks of x,y opposite of humans
#    spl = spl.reshape(xsize, ysize).transpose()
#    #Write interpolated matrix of values to raster
#    band.WriteArray(spl, 0, 0)

    def test_waveEnergy_wavePower(self):
        """Test wavePower to make sure desired outputs are met"""
        filesystemencoding = sys.getfilesystemencoding()

        testDir = './data/test_data/wave_Energy'
        path = testDir + os.sep + 'test_output/wpGen.tif'
        whPath = testDir + os.sep + 'test_output/wheight.tif'
        wpPath = testDir + os.sep + 'test_output/wperiod.tif'
        ePath = testDir + os.sep + 'test_output/elevation.tif'
        #Add the Output directory onto the given workspace
        output_dir = testDir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        waveHeightDriver = gdal.GetDriverByName('GTIFF')
        waveHeight = waveHeightDriver.Create(whPath, 5, 5, 1, gdal.GDT_Float32)
        waveHeight.SetGeoTransform([-129, 1, 0, 48, 0, -1])
        waveHeight.GetRasterBand(1).Fill(2)
        waveHeight.GetRasterBand(1).SetNoDataValue(0)

        wavePeriodDriver = gdal.GetDriverByName('GTIFF')
        wavePeriod = wavePeriodDriver.Create(wpPath, 5, 5, 1, gdal.GDT_Float32)
        wavePeriod.SetGeoTransform([-129, 1, 0, 48, 0, -1])
        wavePeriod.GetRasterBand(1).Fill(5)
        wavePeriod.GetRasterBand(1).SetNoDataValue(0)

        elevationDriver = gdal.GetDriverByName('GTIFF')
        elevation = elevationDriver.Create(ePath, 5, 5, 1, gdal.GDT_Float32)
        elevation.SetGeoTransform([-129, 1, 0, 48, 0, -1])
        elevation.GetRasterBand(1).Fill(-500)
        elevation.GetRasterBand(1).SetNoDataValue(0)

        waveEnergy_core.wavePower(waveHeight, wavePeriod, elevation, path)
        wpRaster = gdal.Open(path, GA_Update)
        matrix = wpRaster.GetRasterBand(1).ReadAsArray()
        self.assertAlmostEqual(matrix[0][0], 8.44585, 4)

#        def wavePower(waveHeight, wavePeriod, elevation, wavePowerPath, blankRaster):
#            p = 1028
#            g = 9.8
#            alfa = 0.86
#            def op(a, b, c, d):
#                c = np.absolute(c)
#                tem = 2.0 * math.pi / (b * alfa)
#                k = np.square(tem) / (g * np.sqrt(np.tanh((np.square(tem)) * (c / g))))
#                waveGroupVelocity = ((1 + ((2 * k * c) / np.sinh(2 * k * c))) * (np.sqrt((g / k) * np.tanh(k * c)))) / 2
#                wp = (((p * g) / 16) * (np.square(a)) * waveGroupVelocity) / 1000
#                return wp
#        
#            invest_core.vectorizeRasters([waveHeight, wavePeriod, elevation, blankRaster], op,
#                                         rasterName=wavePowerPath, datatype=gdal.GDT_Float32)
#            
#            wpRaster = gdal.Open(wavePowerPath, GA_Update)
#            wpNoData = wpRaster.GetRasterBand(1).GetNoDataValue()
#            def op2(a):
#                if a < 1:
#                    return wpNoData
#                else:
#                    return a
#            invest_core.vectorize1ArgOp(wpRaster.GetRasterBand(1), op2, wpRaster.GetRasterBand(1))

#    def test_waveEnergy_with_inputs(self):
#        """Test timber model with real inputs.  Compare copied and modified shapefile with valid
#            shapefile that was created from the same inputs.  Regression test."""
#        #Open table and shapefile
#        attr_table = dbf.Dbf('./data/timber/input/plant_table.dbf')
#        test_shape = ogr.Open('./data/timber/input/plantation.shp', 1)
#
#        #Add the Output directory onto the given workspace
#        output_dir = './data/test_data/timber' + os.sep + 'Output/'
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
#        timber_output_shape = ogr.Open('./data/test_data/timber/Output/timber.shp', 1)
#        timber_output_layer = timber_output_shape.GetLayerByName('timber')
#
#        args = {'timber_shape': timber_output_shape,
#               'attr_table':attr_table,
#               'mdr':7,
#               }
#
#        timber_core.execute(args)
#
#        valid_output_shape = ogr.Open('./data/timber/sample_output/timber.shp')
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
#        if os.path.isdir('./data/test_data/timber/Output/'):
#            textFileList = os.listdir('./data/test_data/timber/Output/')
#            for file in textFileList:
#                os.remove('./data/test_data/timber/Output/' + file)
#            os.rmdir('./data/test_data/timber/Output/')
