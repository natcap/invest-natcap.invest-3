from osgeo import gdal
from osgeo import osr

import numpy as np

##import os
##
##if not ('GDAL_PATH' in os.environ):
##    os.environ['GDAL_PATH'] = '/usr/share/gdal/1.9/'

def matrix_to_dataset_uri(matrix, dataset_uri):
    rows = len(matrix)
    cols = len(matrix[0])
    
    driver = gdal.GetDriverByName("GTiff")
    dataset_type = gdal.GDT_Int16
    dataset = driver.Create(dataset_uri, cols, rows, 1, dataset_type)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(26711)
    dataset.SetProjection(srs.ExportToWkt())

    origin_x = 444720
    scale_x = 30
    theta_y = 0
    origin_y = 3751320
    theta_x = 0
    scale_y = -30

    geo_transform = [origin_x, scale_x, theta_y, origin_y, theta_x, scale_y]
    dataset.SetGeoTransform(geo_transform)

    dataset.GetRasterBand(1).WriteArray(np.array(matrix))
    dataset.GetRasterBand(1).SetNoDataValue(-1)

    dataset = None
