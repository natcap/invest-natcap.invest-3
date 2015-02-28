from osgeo import gdal, ogr, osr


def create_raster(filepath, orgX, orgY, pixWidth, pixHeight, array, proj=4326, gdal_type=gdal.GDT_Float32, nodata=-9999):
    '''

    Args:
        filepath (str): Path to output Geotiff file
        orgX (float): Western edge? Left-most edge?
        orgY (float): Northern edge? Top-most edge?
        pixWidth (float): Width of each pixel in given projection's units
        pixHeight (float): Height of each pixel in given projection's units
        array (np.array): Two-dimensional NumPy array

    Keyword Args:
        proj (int): EPSG projection, default 4326
        gdal_type (type): A GDAL Datatype, default gdal.GDT_Float32
        nodata ((should match the provided GDT)): nodata value, default -9999.0

    Returns:
        None
    '''
    assert(len(array.shape) == 2)
    assert(orgY >= array.shape[1])

    num_bands = 1
    rotX = 0.0
    rotY = 0.0

    rows = array.shape[1]
    cols = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    raster = driver.Create(filepath, cols, rows, num_bands, gdal_type)
    raster.SetGeoTransform((orgX, pixWidth, rotX, orgY, rotY, pixHeight))

    band = raster.GetRasterBand(1)  # Get only raster band
    band.SetNoDataValue(nodata)
    band.WriteArray(array.T)
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromEPSG(proj)
    raster.SetProjection(raster_srs.ExportToWkt())
    band.FlushCache()

    driver = None
    raster = None
    band = None
