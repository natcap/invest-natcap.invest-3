try:
    print('Trying to import.')
    from osgeo import gdal
    raw_input('Imported! (Press enter)')
except Exception, e:
    print(e)
    raw_input('Failed! (Press enter)')
