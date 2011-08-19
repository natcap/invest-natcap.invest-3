try:
    print('Trying to import.')
    import os
    os.environ['PATH'] = 'C:\\OSGeo4W\\bin;' + os.environ['PATH']
    newpath = ""
    for p in os.environ['PATH'].split(';'):
        if 'ArcGIS' not in p:
            newpath += p + ';'
    os.environ['PATH'] = newpath
    print("\n".join(sorted(os.environ['PATH'].split(';'))))
    import sys
    print("\n".join(sorted(sys.path)))
    from osgeo import gdal
    raw_input('Imported! (Press enter)')
except Exception, e:
    print(e)
    raw_input('Failed! (Press enter)')
