"""This reads in the CSV table of methods/parameters by grid-cell and creates a
    point shapefile of those locations"""

import os

import gdal
import ogr
import osr
import pygeoprocessing

def main():
    """main entry point"""


    table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\carbon_edge_effect\carbon_edge_regression_coefficients.csv"
    regression_table = pygeoprocessing.get_lookup_from_table(table_uri, 'id')

    raster_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\carbon_edge_effect\edge_carbon_lu_sample_map.tif"
    raster_ds = gdal.Open(raster_uri)

    ds_projection_wkt = raster_ds.GetProjection()
    output_sr = osr.SpatialReference()
    output_sr.ImportFromWkt(ds_projection_wkt)

    wgs84_sr = osr.SpatialReference()
    wgs84_sr.SetWellKnownGeogCS("WGS84")

    coord_trans = osr.CoordinateTransformation(wgs84_sr, output_sr)

    print regression_table[118]
    print coord_trans.TransformPoint(
        regression_table[118]['meanlon'], regression_table[118]['meanlat'])

    grid_points_uri = 'grid_points.shp'

    if os.path.isfile(grid_points_uri):
        os.remove(grid_points_uri)

    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    grid_points_datasource = output_driver.CreateDataSource(
        grid_points_uri)


    grid_points_layer = grid_points_datasource.CreateLayer(
        'grid_points', output_sr, ogr.wkbPoint)

    grid_points_layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    for grid_id in regression_table:
        grid_coords = coord_trans.TransformPoint(
            regression_table[grid_id]['meanlon'],
            regression_table[grid_id]['meanlat'])
        point_geometry = ogr.Geometry(ogr.wkbPoint)
        point_geometry.AddPoint(grid_coords[0], grid_coords[1])

        # Get the output Layer's Feature Definition
        feature_def = grid_points_layer.GetLayerDefn()
        grid_point_feature = ogr.Feature(feature_def)
        grid_point_feature.SetGeometry(point_geometry)
        grid_point_feature.SetField(0, grid_id)
        grid_points_layer.CreateFeature(grid_point_feature)

    #import scipy
    #scipy.interpolate.griddata(points, values, xi, method='linear', fill_value=nan)[source]

if __name__ == '__main__':

    main()
