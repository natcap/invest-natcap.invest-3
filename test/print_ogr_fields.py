'''This is going to get data from shape files, and do something with them.'''

import os

from osgeo import ogr


#Open this file, this will return a data set, returns a gdal DataSet
#Note, can have a second param there that allows the file to be writable
ds = ogr.Open('data/aquaculture_data/Finfish_Netpens.shp')
dr = ogr.GetDriverByName('ESRI Shapefile')

#need to delete the previous version of the ds before you can create a 
#new one, won't overwrite
path = 'data/aquaculture_data/finfish_out_copy.shp'

if (os.path.isfile(path)):
    os.remove(path)

ds_copy = dr.CopyDataSource(ds, path)

#layer = ds.GetLayer()
#layer.ResetReading()

layer = ds_copy.GetLayer()
#in order to create a new field, first need to write a field definition
field_defn = ogr.FieldDefn('AREA_SQKM', ogr.OFTReal)
layer.CreateField(field_defn)

for feature in layer:
    print feature.items()
    area_m = feature.items()['AREA_SQM']
    area_km = area_m /1000 ** 2
    
    feature.SetField('AREA_SQKM', area_km)
    #need to commit to the database of the features
    layer.SetFeature(feature)
#print layer
