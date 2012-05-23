import sys

from osgeo import gdal
from osgeo import ogr

#This craziness is just for development to import a relative link so I can
#run in the current directory that has a soft link.
try:
    from invest_natcap import raster_utils
except:
    import raster_utils

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'usage:\n %s AOIPolygonFile PointFile PointAttribute' \
            % sys.argv[0]
        sys.exit(-1)

    aoi_ds = ogr.Open(sys.argv[1])
    point_ds = ogr.Open(sys.argv[2])
    attribute = sys.argv[3]
