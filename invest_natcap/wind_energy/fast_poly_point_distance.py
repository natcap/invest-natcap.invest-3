import sys

from osgeo import ogr
import shapely.wkt
import shapely.ops
from shapely import speedups
speedups.enable()


point_shape = ogr.Open('../../test/data/wind_energy_regression_data/wind_points_clipped.shp')
poly_shape = ogr.Open('../../test/data/wind_energy_regression_data/global_poly_clip.shp')

point_layer = point_shape.GetLayer()
point_object = []

print 'load points'
poly_layer = poly_shape.GetLayer()
poly_list = []
count = 1
for feat in poly_layer:
    print feat, count
    shapely_polygon = shapely.wkt.loads(feat.GetGeometryRef().ExportToWkt())
    poly_list.append(shapely_polygon.simplify(0.1, preserve_topology=False))

print 'do union'
multi_polygon = shapely.ops.unary_union(poly_list)

print 'load points'
point_list = []
for feat in point_layer:
    shapely_point = shapely.wkt.loads(feat.GetGeometryRef().ExportToWkt())
    point_list.append(shapely_point)

print 'find distances'
distances = []
for point in point_list:
    d = point.distance(multi_polygon)
    print d
    distances.append(d)

