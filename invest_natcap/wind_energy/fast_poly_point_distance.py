import sys
from shapely import speedups

speedups.enable()

from matplotlib import pyplot
from shapely.geometry import Point
from descartes import PolygonPatch

from osgeo import ogr
from shapely.geometry import Polygon, Point, MultiPolygon, MultiPoint
from shapely.wkt import dumps, loads
import shapely.ops


point_shape = ogr.Open('wind_points_clipped.shp')
poly_shape = ogr.Open('global_poly_clip.shp')

point_layer = point_shape.GetLayer()

point_object = []

print 'load points'
multi_polygon = None
poly_layer = poly_shape.GetLayer()

poly_list = []
print 'load list'
count = 1
for feat in poly_layer:

    print feat, count
    shapely_polygon = loads(feat.GetGeometryRef().ExportToWkt())
    poly_list.append(shapely_polygon.simplify(0.01, preserve_topology=False))
    count += 1
    #if count == 0: break

print 'do union'
multi_polygon = shapely.ops.unary_union(poly_list)

#sys.exit(0)

print 'load points'
point_list = []
for feat in point_layer:
    shapely_point = loads(feat.GetGeometryRef().ExportToWkt())
    point_list.append(shapely_point)

print 'multi point it'
#multi_point = MultiPoint(point_list)
#print multi_point
print 'muliti distance it'
#print multi_point.distance(multi_polygon)

#print multi_polygon

distances = []

print 'find distances'

dist_list = []
for point in point_list:
    d = point.distance(multi_polygon)
    print d
    distances.append(d)

#print distances

