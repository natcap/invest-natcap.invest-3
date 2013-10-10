import os

import gdal
import osr
import numpy

if __name__ == '__main__':

    ascii_raster_uri = 'sugarcane_harea.asc'
    ascii_file = open(ascii_raster_uri, 'r')
    ascii_headers = [
        'ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'NODATA_value']

    raster_properties = {}
    for header in ascii_headers:
        line = ascii_file.readline().split()
        print line
        if line[0] != header:
            raise Exception('Expected %s but encountered %s' % (header, line[0]))
        raster_properties[line[0]] = float(line[1])
    print raster_properties
        
    out_array = numpy.zeros(
        (raster_properties['nrows'], raster_properties['ncols']))
    
    output_uri = os.path.splitext(os.path.basename(ascii_raster_uri))[0] + '.tif'

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(
        output_uri.encode('utf-8'), int(raster_properties['ncols']), int(raster_properties['nrows']), 1, gdal.GDT_Float32)

    dataset.SetGeoTransform(
        [raster_properties['xllcorner'], raster_properties['cellsize'], 0.0,
        raster_properties['yllcorner'] + raster_properties['cellsize'] * raster_properties['nrows'], 0.0, -raster_properties['cellsize']]) 
    spat_ref = osr.SpatialReference()
    spat_ref.SetWellKnownGeogCS("WGS84")
    dataset.SetProjection(spat_ref.ExportToWkt())
        
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(raster_properties['NODATA_value'])
    
    rows = numpy.array(ascii_file.read().split(), dtype=numpy.float)
    matrix =  rows.reshape((raster_properties['nrows'], raster_properties['ncols']))
    band.WriteArray(matrix)