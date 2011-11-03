import unittest
import imp, sys, os
import timber_core
import math
import numpy as np
from dbfpy import dbf
from osgeo import ogr

class TestTimber(unittest.TestCase):

    def test_timber_summationOne_NotImmedHarv(self):
        """Test of the first summation in the Net Present Value equation when 
            immediate harvest is NO. Using known inputs.  Calculated value and Hand Calculations
            compared against the models equation"""
        mdr_perc = 1.07
        harvest_value = 3990.0
        freq_Harv = 2
        num_Years = 4
        upper_limit = int(math.floor(num_Years/freq_Harv))
        lower_limit = 1
        subtractor = 1
        
        summationCalculatedByHand = 6986.000492
        summation = timber_core.npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
    
        summationCalculated = 0.0
        for num in range(lower_limit, upper_limit+1):
            summationCalculated = summationCalculated + (harvest_value/((1.07)**((freq_Harv*num)-subtractor)))
            
        self.assertAlmostEqual(summationCalculatedByHand, summation, 5)
        self.assertAlmostEqual(summationCalculated, summation, 5)
        
        
    def test_timber_summationOne_ImmedHarv(self):  
        """Test of the first summation in the Net Present Value equation when 
            immediate harvest is YES. Using known inputs.  Calculated value and Hand Calculations
            compared against the models equation"""
        mdr_perc = 1.07
        harvest_value = 3990.0
        freq_Harv = 2
        num_Years = 4
        upper_limit = int(math.ceil((num_Years/freq_Harv)-1.0))
        lower_limit = 0
        subtractor = 0
        
        summationCalculatedByHand = 7475.020526
        summation = timber_core.npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
        
        summationCalculated = 0.0
        for num in range(lower_limit, upper_limit+1):
            summationCalculated = summationCalculated + (harvest_value/((1.07)**((freq_Harv*num)-subtractor)))
            
        self.assertAlmostEqual(summationCalculatedByHand, summation, 5)
        self.assertAlmostEqual(summationCalculated, summation, 5)
        
    def test_timber_summationTwo(self):
        """Test of the second summation in the Net Present Value equation using 
            known inputs.  Calculated value and Hand Calculations
            compared against the models equation"""
        lower_limit = 0
        upper_limit = 3
        maint_Cost = 100
        mdr_perc = 1.07
        
        summationCalculatedByHand = 362.4316044
        summation = timber_core.npvSummationTwo(lower_limit, upper_limit, maint_Cost, mdr_perc)
        
        summationCalculated = 0.0
        for num in range(0, 4):
            summationCalculated = summationCalculated + (maint_Cost/((1.07)**num))
            
        self.assertAlmostEqual(summationCalculatedByHand, summation, 5)
        self.assertAlmostEqual(summationCalculated, summation, 5)        
        
    def test_timber_smoke(self):
        """Smoke test for Timber.  Model should not crash with 
            basic input requirements"""
        #Set the path for the test inputs/outputs and check to make sure the directory does not exist
        smoke_path = '../../test_data/timber/Smoke/'

        if not os.path.isdir(smoke_path):
            os.mkdir('../../test_data/timber/Smoke')
        #Define the paths for the sample input/output files
        dbf_path = '../../test_data/timber/Smoke/test.dbf'
        shp_path = '../../test_data/timber/Smoke'

        
        #Create our own dbf file with basic attributes for one polygon
        db = dbf.Dbf(dbf_path, new=True)
        db.addField( ('PRICE', 'N', 3), ('T', 'N', 2), ('BCEF', 'N', 1), ('Parcel_ID', 'N', 1),
                     ('Parcl_area', 'N', 4), ('Perc_harv', 'N', 2), ('Harv_mass', 'N', 3), 
                     ('Freq_harv', 'N', 2), ('Maint_cost', 'N', 3), ('Harv_cost', 'N', 3), ('Immed_harv', 'C', 1))
        rec = db.newRecord()
        rec['PRICE'] = 100
        rec['T'] = 2
        rec['BCEF'] = 1
        rec['Parcel_ID'] = 1
        rec['Parcl_area'] = 1
        rec['Perc_harv'] = 10
        rec['Harv_mass'] = 100
        rec['Freq_harv'] = 1
        rec['Maint_cost'] = 0
        rec['Harv_cost'] = 0
        rec['Immed_harv'] = 'Y'
        rec.store()
        db.close()
        
        #Create our own basic shapefile with one polygon to run through the model
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        ds = drv.CreateDataSource(shp_path)
        lyr = ds.CreateLayer('timber', None, ogr.wkbPolygon)
        
        #Creating a field because OGR will not allow an empty feature, it will default by putting FID_1
        #as a field.  OGR will also self create the FID and Shape field.
        field_defn = ogr.FieldDefn('Parcl_ID', ogr.OFTInteger )
        lyr.CreateField(field_defn)
        
        feat = ogr.Feature(lyr.GetLayerDefn())
        lyr.CreateFeature(feat)
        index = feat.GetFieldIndex('Parcl_ID')
        feat.SetField(index, 1)       

        #save the field modifications to the layer.
        lyr.SetFeature(feat)
        feat.Destroy()

        db = dbf.Dbf(dbf_path)

        #Arguments to be past to the model
        args= {'timber_shape': ds,
               'attr_table':db, 
               'mdr':7, 
               }
        
        timber_core.execute(args)
        
        #Hand calculated values for the above inputs.
        #To be compared with the timber model's output of the created shapefile.
        tnpv = 1934.579439
        tbio = 20
        tvol = 20
        
        feat = lyr.GetFeature(0)
        for field, value in ( ('TNPV', tnpv), ('TBiomass', tbio), ('TVolume', tvol)):
            field_index = feat.GetFieldIndex(field)
            field_value = feat.GetField(field_index)
            self.assertAlmostEqual(value, field_value, 6)        
        
        #This is how OGR closes its datasources
        ds = None
        db.close()
        
        #Remove the generated output from the smoke test
        if os.path.isdir(smoke_path):
            textFileList = os.listdir(smoke_path)
            for file in textFileList:
                os.remove(smoke_path+file)
            os.rmdir(smoke_path)
   
    def test_timber_BioVol(self):
        """Biomass and Volume test for timber model.  Creates an attribute table and shapefile
        with set values.  Compares calculated Biomass and Volume with that from running the
        shapefile through the model. """
        #Set the path for the test inputs/outputs and check to make sure the directory does not exist
        dir_path = '../../test_data/timber/Test/'
        if not os.path.isdir(dir_path):
            os.mkdir('../../test_data/timber/Test')
        shp_path = '../../test_data/timber/Test'
        dbf_path = '../../test_data/timber/Test/test.dbf'
        
        #Create our own dbf file with basic attributes for one polygon
        db = dbf.Dbf(dbf_path, new=True)
        db.addField( ('PRICE', 'N', 3), ('T', 'N', 2), ('BCEF', 'N', 1), ('Parcel_ID', 'N', 1),
                     ('Parcl_area', 'N', 4), ('Perc_harv', 'N', 2), ('Harv_mass', 'N', 3), 
                     ('Freq_harv', 'N', 2), ('Maint_cost', 'N', 3), ('Harv_cost', 'N', 3), ('Immed_harv', 'C', 1))
        rec = db.newRecord()
        rec['PRICE'] = 400
        rec['T'] = 4
        rec['BCEF'] = 1
        rec['Parcel_ID'] = 1
        rec['Parcl_area'] = 800
        rec['Perc_harv'] = 10.0
        rec['Harv_mass'] = 100
        rec['Freq_harv'] = 2
        rec['Maint_cost'] = 100
        rec['Harv_cost'] = 100
        rec['Immed_harv'] = 'Y'
        rec.store()
        db.close()
        #Set some variable needed for Biomass/Volume calculations from created attr. table.
        db = dbf.Dbf(dbf_path)
        parcl_Area = db[0]['Parcl_area']
        perc_Harv = float(db[0]['Perc_harv'])
        harv_Mass = db[0]['Harv_mass']
        num_Years = db[0]['T']
        freq_Harv = db[0]['Freq_harv']
        BCEF = db[0]['BCEF']
        #Calculate Biomass,Volume, and TNPV by hand to 3 decimal places.
        calculatedBiomass = 16000
        calculatedVolume = 16000
        TNPV = 5690071.137
        #Create our own shapefile with multiple polygons to run through the model
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        ds = drv.CreateDataSource(shp_path)
        lyr = ds.CreateLayer('timber', None, ogr.wkbPolygon)
        
        #Creating a field because OGR will not allow an empty feature, it will default by putting FID_1
        #as a field.  OGR will also self create the FID and Shape field.
        field_defn = ogr.FieldDefn('Parcl_ID', ogr.OFTInteger )
        lyr.CreateField(field_defn)
        
        feat = ogr.Feature(lyr.GetLayerDefn())
        lyr.CreateFeature(feat)
        index = feat.GetFieldIndex('Parcl_ID')
        feat.SetField(index, 1)       
    
        #save the field modifications to the layer.
        lyr.SetFeature(feat)
        feat.Destroy()
        
        #Arguments to be past to the model
        args= {'timber_shape': ds,
               'attr_table':db, 
               'mdr':7, 
               }
        
        timber_core.execute(args)        
        #Compare Biomass and Volume calculations
        feat = lyr.GetFeature(0)
        for field, value in (('TNPV', TNPV), ('TBiomass', calculatedBiomass), ('TVolume', calculatedVolume)):
            field_index = feat.GetFieldIndex(field)
            field_value = feat.GetField(field_index)
            self.assertAlmostEqual(value, field_value, 2)        
        
        #This is how OGR closes its datasources
        ds = None
        lyr = None
        db.close()
        
        #Remove the generated output from the BioVol test
        if os.path.isdir(dir_path):
            textFileList = os.listdir(dir_path)
            i = 0
            for file in textFileList:
                if i==0:
                    i = 1
                else:
                    os.remove(dir_path+file)
            os.rmdir(dir_path)


    def test_timber_with_inputs(self):
        """Test timber model with real inputs.  Compare copied and modified shapefile with valid
            shapefile that was created from the same inputs"""
        
        attr_table = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        test_shape = ogr.Open('../../test_data/timber/input/plantation.shp', 1)
        
        #Add the Output directory onto the given workspace
        output_dir = '../../test_data/timber'+os.sep+'Output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        
        shape_source = output_dir + 'timber.shp'
        
        ogr.GetDriverByName('ESRI Shapefile').\
            CopyDataSource(test_shape, shape_source)
            
        timber_output_shape = ogr.Open('../../test_data/timber/Output/timber.shp', 1)       
        timber_output_layer = timber_output_shape.GetLayerByName('timber')
        
        args= {'timber_shape': timber_output_shape,
               'attr_table':attr_table, 
               'mdr':7, 
               }
        
        timber_core.execute(args)
        
        valid_output_shape = ogr.Open('../../test_data/timber/sample_output/timber.shp')
        valid_output_layer = valid_output_shape.GetLayerByName('timber')
        
        num_features_valid = valid_output_layer.GetFeatureCount()
        num_features_copy  = timber_output_layer.GetFeatureCount()
        self.assertEqual(num_features_valid, num_features_copy)
        
        if num_features_valid == num_features_copy:
            for i in range(num_features_valid):
                feat = valid_output_layer.GetFeature(i)
                feat2 = timber_output_layer.GetFeature(i)
                for field in ('TNPV', 'TBiomass', 'TVolume'):
                    field_index = feat.GetFieldIndex(field)
                    field_value = feat.GetField(field_index)
                    field_index2 = feat2.GetFieldIndex(field)
                    field_value2 = feat2.GetField(field_index2)
                    self.assertAlmostEqual(field_value, field_value2, 2)
        
        valid_output_shape = None
        timber_output_shape = None
        test_shape = None
        timber_output_layer = None
        attr_table.close()
        
        textFileList = os.listdir('../../test_data/timber/Output/')
        
        if os.path.isdir('../../test_data/timber/Output/'):
            for file in textFileList:
                os.remove('../../test_data/timber/Output/'+file)
            os.rmdir('../../test_data/timber/Output/')
  
  
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimber)
    unittest.TextTestRunner(verbosity=2).run(suite)

