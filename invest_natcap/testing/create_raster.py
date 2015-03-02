from osgeo import gdal, osr


def create_raster(filepath, array, topleftX, topleftY, pixWidth=1, pixHeight=1, proj=4326, gdal_type=gdal.GDT_Float32, nodata=-9999):
    '''
    Converts a numpy array to a GeoTIFF file

    Args:
        filepath (str): Path to output GeoTIFF file
        array (np.array): Two-dimensional NumPy array
        topleftX (float): Western edge? Left-most edge?
        topleftY (float): Northern edge? Top-most edge?

    Keyword Args:
        pixWidth (float): Width of each pixel in given projection's units
        pixHeight (float): Height of each pixel in given projection's units
        proj (int): EPSG projection, default 4326
        gdal_type (type): A GDAL Datatype, default gdal.GDT_Float32
        nodata ((should match the provided GDT)): nodata value, default -9999.0

    Returns:
        None
    '''
    assert(len(array.shape) == 2)
    assert(topleftY >= array.shape[1])
    assert(topleftX >= 0)

    num_bands = 1
    rotX = 0.0
    rotY = 0.0

    rows = array.shape[1]
    cols = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    raster = driver.Create(filepath, cols, rows, num_bands, gdal_type)
    raster.SetGeoTransform((topleftX, pixWidth, rotX, topleftY, rotY, (-pixHeight)))

    band = raster.GetRasterBand(1)  # Get only raster band
    band.SetNoDataValue(nodata)
    band.WriteArray(array)
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromEPSG(proj)
    raster.SetProjection(raster_srs.ExportToWkt())
    band.FlushCache()

    driver = None
    raster = None
    band = None
