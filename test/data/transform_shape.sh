#!/bin/bash

#SHPFILEORIG - The source datasource name
SHPFILEORIG=$1
#$CODE - ESPG code to project to
CODE=$2

# You must have a directory in the location of the script call 'transformed'.
# The code below will output the projected datasource into that folder using the
# same name as the input file, but appended with _transformed. This should
# better allow for batching over multiple files

# example : ./transform_shape.sh ../data/cool_shape.shp 4326
# output location : ./transform/cool_shape_transform.shp

ogr2ogr -t_srs EPSG:$CODE ./transformed/`basename $SHPFILEORIG .shp`_transformed.shp $SHPFILEORIG
