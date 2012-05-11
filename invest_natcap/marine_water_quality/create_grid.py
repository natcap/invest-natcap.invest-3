import sys

from osgeo import ogr

try:
    land_poly_file = sys.argv[1]
    aoi_poly_file = sys.argv[2]
    cell_size = int(sys.argv[3])

    land_ds = ogr.Open(land_poly_file)
    aoi_ds = ogr.Open(aoi_poly_file)

    aoi_extent = aoi_ds.GetLayer(0).GetExtent()

    #format of aoi_extent [xleft, xright, ybot, ytop]

    print aoi_extent

except:
    print "Usage create_grid.py land_poly_file aoi_poly_file cell_size"
