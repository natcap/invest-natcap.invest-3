"""This reads in the CSV table of methods/parameters by grid-cell and creates a
    point shapefile of those locations"""

import os

import ogr
import osr

def main():
    """main entry point"""

    grid_points_uri = 'grid_points.shp'

    if os.path.isfile(grid_points_uri):
        os.remove(grid_points_uri)

    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    grid_points_datasource = output_driver.CreateDataSource(
        grid_points_uri)

    output_sr = osr.SpatialReference()
    output_sr.SetWellKnownGeogCS("WGS84")

    grid_points_layer = grid_points_datasource.CreateLayer(
        'grid_points', output_sr, ogr.wkbPoint)

    grid_points_layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))

    point_geometry = ogr.Geometry(ogr.wkbPoint)
    point_geometry.AddPoint(30, 30)

    # Get the output Layer's Feature Definition
    feature_def = grid_points_layer.GetLayerDefn()
    grid_point_feature = ogr.Feature(feature_def)
    grid_point_feature.SetGeometry(point_geometry)
    grid_point_feature.SetField(0, 42)
    grid_points_layer.CreateFeature(grid_point_feature)

    #import scipy
    #scipy.interpolate.griddata(points, values, xi, method='linear', fill_value=nan)[source]

if __name__ == '__main__':
    main()
