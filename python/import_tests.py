try:
    print('Trying to import.')
    import os
    os.environ['PATH'] = 'C:\\OSGeo4W\\bin;' + os.environ['PATH']
    newpath = ""
    for p in os.environ['PATH'].split(';'):
        if 'ArcGIS' not in p:
            newpath += p + ';'
    os.environ['PATH'] = newpath
    #print("\n".join(sorted(os.environ['PATH'].split(';'))))
    import sys
    sys.path.insert(0, "C:\\OSGeo4W\\bin")
    print("\n".join(sys.path))

    print("\n".join(sorted(os.environ.keys())))
    print(os.getcwd())
    os.chdir('C:\\Windows')
    from osgeo import gdal
    raw_input('Imported! (Press enter)')
except Exception, e:
    print(e)
    raw_input('Failed! (Press enter)')
