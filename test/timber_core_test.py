import sys
import os
import unittest
import math
import logging

from osgeo import ogr

from invest_natcap.dbfpy import dbf
from invest_natcap.timber import timber_core

class TestTimber(unittest.TestCase):

    def test_timber_summationOne_NotImmedHarv(self):
        """Test of the first summation in the Net Present Value equation when 
            immediate harvest is NO. Using known inputs.  Calculated value and 
            Hand Calculations compared against the models equation"""
        mdr_perc = 1.07
        harvest_value = 3990.0
        freq_Harv = 2
        num_Years = 4
        upper_limit = int(math.floor(num_Years / freq_Harv))
        lower_limit = 1
        subtractor = 1
        #Calculated value by hand:
        summationCalculatedByHand = 6986.000492
        summation = timber_core.npvSummationOne(
                lower_limit, upper_limit, harvest_value, mdr_perc, 
                freq_Harv, subtractor)

        summationCalculated = 0.0
        for num in range(lower_limit, upper_limit + 1):
            summationCalculated = \
                    summationCalculated + (harvest_value /\
                    ((1.07) ** ((freq_Harv * num) - subtractor)))

        self.assertAlmostEqual(summationCalculatedByHand, summation, 5)
        self.assertAlmostEqual(summationCalculated, summation, 5)


    def test_timber_summationOne_ImmedHarv(self):
        """Test of the first summation in the Net Present Value equation when 
            immediate harvest is YES. Using known inputs.  Calculated value
            and Hand Calculations compared against the models equation"""
        mdr_perc = 1.07
        harvest_value = 3990.0
        freq_Harv = 2
        num_Years = 4
        upper_limit = int(math.ceil((num_Years / freq_Harv) - 1.0))
        lower_limit = 0
        subtractor = 0
        #Calculated value by hand:
        summationCalculatedByHand = 7475.020526
        summation = timber_core.npvSummationOne(
                lower_limit, upper_limit, harvest_value, mdr_perc, 
                freq_Harv, subtractor)

        summationCalculated = 0.0
        for num in range(lower_limit, upper_limit + 1):
            summationCalculated = \
                    summationCalculated + (harvest_value /\
                    ((1.07) ** ((freq_Harv * num) - subtractor)))

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
        #Calculated value by hand:
        summationCalculatedByHand = 362.4316044
        summation = timber_core.npvSummationTwo(
                lower_limit, upper_limit, maint_Cost, mdr_perc)

        summationCalculated = 0.0
        for num in range(0, 4):
            summationCalculated = \
                    summationCalculated + (maint_Cost / ((1.07) ** num))

        self.assertAlmostEqual(summationCalculatedByHand, summation, 5)
        self.assertAlmostEqual(summationCalculated, summation, 5)

    def test_timber_smoke(self):
        """Smoke test for Timber.  Model should not crash with 
            basic input requirements"""
        #Set the path for the test inputs/outputs and check to make sure the
        #directory does not exist
        smoke_path = './invest-data/test/data/test_out/timber/Smoke/'
        if not os.path.isdir(smoke_path):
            os.makedirs(smoke_path)
        #Define the paths for the sample input/output files
        dbf_path = os.path.join(smoke_path, 'test.dbf')
        shp_path = smoke_path
        #Create our own dbf file with basic attributes for one polygon
        db = dbf.Dbf(dbf_path, new=True)
        db.addField(('PRICE', 'N', 3), ('T', 'N', 2), ('BCEF', 'N', 1),
                    ('Parcel_ID', 'N', 1), ('Parcl_area', 'N', 4), 
                    ('Perc_harv', 'N', 2), ('Harv_mass', 'N', 3),
                    ('Freq_harv', 'N', 2), ('Maint_cost', 'N', 3), 
                    ('Harv_cost', 'N', 3), ('Immed_harv', 'C', 1))
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

        #Create our own basic shapefile with one polygon to run through the 
        #model
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        ds = drv.CreateDataSource(shp_path)
        lyr = ds.CreateLayer('timber', None, ogr.wkbPolygon)

        #Creating a field because OGR will not allow an empty feature, 
        #it will default by putting FID_1
        #as a field.  OGR will also self create the FID and Shape field.
        field_defn = ogr.FieldDefn('Parcl_ID', ogr.OFTInteger)
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
        args = {'timber_shape': ds,
               'attr_table':db,
               'mdr':7,
               }

        timber_core.execute(args)

        #Hand calculated values for the above inputs.
        #To be compared with the timber model's output of the created shapefile.
        tnpv = 1934.579439
        tbio = 20
        tvol = 20

        lyr = ds.GetLayerByName('timber')
        feat = lyr.GetFeature(0)
        for field, value in (
                ('TNPV', tnpv), ('TBiomass', tbio), ('TVolume', tvol)):
            field_index = feat.GetFieldIndex(field)
            field_value = feat.GetField(field_index)
            self.assertAlmostEqual(value, field_value, 6)

        #This is how OGR closes and flushes its datasources
        ds.Destroy()
        ds = None
        db.close()

    def test_timber_BioVol(self):
        """Biomass and Volume test for timber model.  Creates an attribute
        table and shapefile with set values.  Compares calculated Biomass
        and Volume with that from running the shapefile through the model. """
        #Set the path for the test inputs/outputs and check to make sure
        #the directory does not exist
        dir_path = './invest-data/test/data/test_out/timber/biovol/Output/'

        #Deleting any files in the output if they already exist, this
        #caused a bug once when I didn't do this.
        if os.path.isdir(dir_path):
            textFileList = os.listdir(dir_path)
            for file in textFileList:
                os.remove(dir_path + file)

        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        shp_path = dir_path
        dbf_path = os.path.join(dir_path, 'test.dbf')

        #Create our own dbf file with basic attributes for one polygon
        db = dbf.Dbf(dbf_path, new=True)
        db.addField(('PRICE', 'N', 3), ('T', 'N', 2), ('BCEF', 'N', 1),
                    ('Parcel_ID', 'N', 1), ('Parcl_area', 'N', 4),
                    ('Perc_harv', 'N', 2), ('Harv_mass', 'N', 3),
                    ('Freq_harv', 'N', 2), ('Maint_cost', 'N', 3),
                    ('Harv_cost', 'N', 3), ('Immed_harv', 'C', 1))
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

        #Calculate Biomass,Volume, and TNPV by hand to 3 decimal places.
        calculatedBiomass = 16000
        calculatedVolume = 16000
        TNPV = 5690071.137
        #Create our own shapefile with a polygon to run through the model
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        ds = drv.CreateDataSource(shp_path)
        lyr = ds.CreateLayer('timber', None, ogr.wkbPolygon)

        #Creating a field because OGR will not allow an empty feature,
        #it will default by putting FID_1
        #as a field.  OGR will also self create the FID and Shape field.
        field_defn = ogr.FieldDefn('Parcl_ID', ogr.OFTInteger)
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
        args = {'timber_shape': ds,
               'attr_table':db,
               'mdr':7,
               }

        timber_core.execute(args)
        #Compare Biomass, Volume, and TNPV calculations
        lyr = ds.GetLayerByName('timber')
        feat = lyr.GetFeature(0)
        for field, value in (
                ('TNPV', TNPV), ('TBiomass', calculatedBiomass),
                ('TVolume', calculatedVolume)):
            field_index = feat.GetFieldIndex(field)
            field_value = feat.GetField(field_index)
            self.assertAlmostEqual(value, field_value, 2)

        #This is how OGR closes and flushes its datasources
        ds.Destroy()
        ds = None
        lyr = None
        db.close()

    def test_timber_with_inputs(self):
        """Test timber model with real inputs. Compare copied and 
            modified shapefile with valid shapefile that was created from
            the same inputs.  Regression test."""
        #Open table and shapefile
        input_dir = './invest-data/test/data/timber/input/'
        out_dir = './invest-data/test/data/test_out/timber/with_inputs/'
        attr_table = dbf.Dbf(os.path.join(input_dir, 'plant_table.dbf'))
        test_shape = ogr.Open(os.path.join(input_dir, 'plantation.shp'), 1)

        #Add the Output directory onto the given workspace
        output_uri = os.path.join(out_dir, 'timber.shp')
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        if os.path.isfile(output_uri):
            os.remove(output_uri)

        shape_source = output_uri

        ogr.GetDriverByName('ESRI Shapefile').\
            CopyDataSource(test_shape, shape_source)

        timber_output_shape = ogr.Open(shape_source, 1)
        timber_output_layer = timber_output_shape.GetLayerByName('timber')

        args = {'timber_shape': timber_output_shape,
               'attr_table':attr_table,
               'mdr':7,
               }

        timber_core.execute(args)

        valid_output_shape = ogr.Open(
                './invest-data/test/data/timber/regression_data/timber.shp')
        valid_output_layer = valid_output_shape.GetLayerByName('timber')
        #Check that the number of features (polygons) are the same between
        #shapefiles
        num_features_valid = valid_output_layer.GetFeatureCount()
        num_features_copy = timber_output_layer.GetFeatureCount()
        self.assertEqual(num_features_valid, num_features_copy)
        #If number of features are equal, compare each shapefiles 3 fields
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
        #This is how OGR cleans up and flushes datasources
        test_shape.Destroy()
        timber_output_shape.Destroy()
        valid_output_shape = None
        timber_output_shape = None
        test_shape = None
        timber_output_layer = None
        attr_table.close()
