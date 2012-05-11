import sys

from osgeo import ogr

try:
    land_poly_file = sys.argv[1]
    aoi_poly_file = sys.argv[2]
    cell_size = int(sys.argv[3])

    land_ds = ogr.Open(land_poly_file)
    aoi_ds = ogr.Open(aoi_poly_file)

    #format of aoi_extent [xleft, xright, ybot, ytop]
    aoi_extent = aoi_ds.GetLayer(0).GetExtent()
    xleft,xright,ybot,ytop = aoi_extent

    x_ticks = int((xright-xleft)/cell_size)
    y_ticks = int((ytop-ybot)/cell_size)

    print aoi_extent
    print x_ticks, y_ticks

    for x_index in range(x_ticks):
        for y_index in range(y_ticks):
            x_coord = xleft+x_index*cell_size
            y_coord = ytop-y_index*cell_size

except:
    print "Usage create_grid.py land_poly_file aoi_poly_file cell_size"
