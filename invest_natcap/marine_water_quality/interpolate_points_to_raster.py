import sys

from osgeo import gdal
from osgeo import ogr


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'usage:\n %s AOIPolygonFile PointFile PointAttribute' \
            % sys.argv[0]
        sys.exit(-1)

    aoi_ds = ogr.Open(sys.argv[1])
    point_ds = ogr.Open(sys.argv[2])
    attribute = sys.argv[3]

    print aoi_ds, point_ds, attribute
