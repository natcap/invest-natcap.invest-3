#!/bin/bash
SHPFILE=$1
BASE=`basename $SHPFILE .shp`
EXTENT=`ogrinfo -so $SHPFILE $BASE | grep Extent \
    | sed 's/Extent: //g' | sed 's/(//g' | sed 's/)//g' \
    | sed 's/ - /, /g'`
EXTENT=`echo $EXTENT | awk -F ',' '{print $1 " " $4 " " $3 " " $2}'`
echo $EXTENT

RASTERFILE=$2
gdal_translate -projwin $EXTENT -of GTiff $RASTERFILE ./clip/`basename $RASTERFILE .sid`_clip.tif


