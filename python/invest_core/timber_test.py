import unittest
import imp, sys, os
import timber
import math
import numpy as np
from dbfpy import dbf

from osgeo import ogr, gdal
from osgeo.gdalconst import *

class TestTimber(unittest.TestCase):

    def test_timber_getBiomass(self):
        parcl_Area = 1200
        perc_Harv = 10.0
        harv_Mass = 150
        num_Years = 50.0
        freq_Harv = 10
        
        TBiomass = timber.getBiomass(parcl_Area, perc_Harv, harv_Mass, num_Years, freq_Harv)
        
        calculatedBiomassByHand = 90000
        
        calculatedBiomass = parcl_Area * (perc_Harv/100) * harv_Mass * math.ceil(num_Years/freq_Harv)
        
        self.assertEqual(calculatedBiomass, TBiomass)
        self.assertEqual(TBiomass, calculatedBiomass)
        
    def test_timber_getVolume(self):
        biomass = 90000
        BCEF = 1.0
        
        TVolume = timber.getVolume(biomass, BCEF)
        
        calculatedVolumeByHand = 90000
        
        calculatedVolume = biomass * (1/BCEF)
        
        self.assertEqual(calculatedVolumeByHand, TVolume)
        self.assertEqual(calculatedVolume, TVolume)
        
    def test_timber_harvestValue(self):
        parcl_Area = 1200
        perc_Harv = 10.0
        harv_Mass = 150
        harv_Cost = 100
        price = 615
        
        harvest_value = timber.harvestValue(perc_Harv, price, harv_Mass, harv_Cost)
        
        harvestValueCalculatedByHand = 9215.00
        
        harvestValueCalculated = (perc_Harv/100)*((price*harv_Mass)-harv_Cost)
        
        self.assertEqual(harvest_value, harvestValueCalculatedByHand)
        self.assertEqual(harvest_value, harvestValueCalculated)
        
    def test_timber_summationOne_NotImmedHarv(self):
 
        mdr_perc = 1.07
        harvest_value = 9215.00
        freq_Harv = 10
        num_Years = 50
        upper_limit = int(math.floor(freq_Harv/num_Years))
        lower_limit = 1
        subtractor = 1
        
        summation = timber.npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
    
        summation_calculated = 0.0
        for num in range(lower_limit, upper_limit+1):
            summation_calculated = summation_calculated + (harvest_value/((1.07)**((freq_Harv*num)-subtractor)))
            
        self.assertAlmostEqual(summation_calculated, summation, 15)
        
        
    def test_timber_summationOne_ImmedHarv(self):  
        mdr_perc = 1.07
        harvest_value = 4698.6
        freq_Harv = 6
        num_Years = 50
        upper_limit = int(math.ceil((num_Years/freq_Harv)-1.0))
        lower_limit = 0
        subtractor = 0
    
        summation = timber.npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
        
        summation_calculated = 0.0
        for num in range(lower_limit, upper_limit+1):
            summation_calculated = summation_calculated + (harvest_value/((1.07)**((6*num)-subtractor)))
        self.assertAlmostEqual(summation_calculated, summation, 15)
        
    def test_timber_summationTwo(self):
                
        lower_limit = 0
        upper_limit = 49
        maint_Cost = 100
        mdr_perc = 1.07

        summation = timber.npvSummationTwo(lower_limit, upper_limit, maint_Cost, mdr_perc)
        
        summation_calculated = 0.0
        for num in range(0, 50):
            summation_calculated = summation_calculated + (100/((1.07)**num))
            
        self.assertAlmostEqual(summation_calculated, summation, 15)
        
    def test_timber_smoke(self):
        dbf_path = '../../test_data/timber/test.dbf'
        shp_path = '../../test_data/timber/'
        os.mkdir('../../test_data/timber/Output')
        
        db = dbf.Dbf(dbf_path, new=True)
        db.addField( ('OID', 'N', 1), ('PRICE', 'N', 3), ('T', 'N', 2), ('BCEF', 'N', 1), ('Parcel_ID', 'N', 1),
                     ('Parcl_area', 'N', 4), ('Perc_harv', 'N', 2), ('Harv_mass', 'N', 3), 
                     ('Freq_harv', 'N', 2), ('Maint_cost', 'N', 3), ('Harv_cost', 'N', 3), ('Immed_harv', 'C', 1))
        rec = db.newRecord()
        rec['OID'] = 0
        rec['PRICE'] = 1
        rec['T'] = 5
        rec['BCEF'] = 1
        rec['Parcel_ID'] = 1
        rec['Parcl_area'] = 1
        rec['Perc_harv'] = 1
        rec['Harv_mass'] = 1
        rec['Freq_harv'] = 1
        rec['Maint_cost'] = 1
        rec['Harv_cost'] = 1
        rec['Immed_harv'] = 'N'
        rec.store()
        db.close()
        
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        ds = drv.CreateDataSource(shp_path)
        lyr = ds.CreateLayer('plantation', None, ogr.wkbUnknown)
        feat = ogr.Feature(lyr.GetLayerDefn())
        lyr.CreateFeature(feat)
        feat.Destroy()
        
        ds = None
        
        timber_shp_copy = ogr.Open('../../test_data/timber/plantation.shp', 1)
        timber_layer_copy = timber_shp_copy.GetLayerByName('plantation')
        
        db = dbf.Dbf(dbf_path)
        
        args= {'timber_shape_loc': shp_path,
               'output_dir': '../../test_data/timber/Output',
               'plant_prod_loc': dbf_path,
               'plant_prod':db, 
               'mdr':7, 
               'timber_layer_copy': timber_layer_copy,
               'timber_shp_copy': timber_shp_copy 
               }
        
        timber.execute(args)

        db.close()
        timber_shp_copy = None
        
        os.remove(dbf_path)
        os.remove('../../test_data/timber/plantation.shp')
        os.remove('../../test_data/timber/plantation.shx')
        os.remove('../../test_data/timber/plantation.dbf')
        
        pass
        
    def test_timber_with_inputs(self):
        plant_file = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        plant_shape = ogr.Open('../../test_data/timber/input/plantation.shp', 1)
        
        ogr.GetDriverByName('ESRI Shapefile').\
            CopyDataSource(plant_shape, '../../test_data/timber/Output' + os.sep)
            
        timber_shp_copy = ogr.Open('../../test_data/timber/output/plantation.shp', 1)
       
        timber_layer_copy = timber_shp_copy.GetLayerByName('plantation')
        
        args= {'timber_shape_loc': '../../test_data/timber/input/plantation.shp',
               'output_dir': '../../test_data/timber/Output',
               'plant_prod_loc': '../../test_data/timber/input/plant_table.dbf',
               'plant_prod':plant_file, 
               'mdr':7, 
               'timber_layer_copy': timber_layer_copy,
               'timber_shp_copy': timber_shp_copy 
               }
        
        total_dict = timber.execute(args)
        
        timber_shp_copy = None
        plant_shape = None
        plant_file.close()
        
        textFileList = os.listdir('../../test_data/timber/Output/')
        
        if os.path.isdir('../../test_data/timber/Output/'):
            for file in textFileList:
                os.remove('../../test_data/timber/Output/'+file)
            os.rmdir('../../test_data/timber/Output/')
            
        pass
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimber)
    unittest.TextTestRunner(verbosity=2).run(suite)

