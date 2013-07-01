from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import os

def execute(args):
    #inputs
    workspace_dir = args["workspace_dir"]
    lulc1_uri = args["lulc1_uri"]
    lulc2_uri = args["lulc2_uri"]
    carbon_uri = args["carbon_pools_uri"]
    transition_matrix_uri = args["transition_matrix_uri"]

    #intermediate
    carbon_per_area_uri = os.path.join(workspace_dir, "cpa.tif")
    habitat_area_uri = os.path.join(workspace_dir, "ha.tif")
    carbon_storage_uri = os.path.join(workspace_dir, "cs.tif")
    transition_uri = os.path.join(workspace_dir, "t.tif")

    #construct op from carbon storage table
    carbon_file = open(carbon_uri)
    #skip header
    carbon_file.readline()
    #parse table
    carbon_dict={}
    for line in carbon_file:
        lulc_code, name, above, below, soil, litter = line.strip().split(",")
        carbon_dict[int(lulc_code)] = [float(above), float(below),
                                  float(soil), float(litter)]
    carbon_file.close()

    #create carbon storage raster for t1
    nodata = raster_utils.get_nodata_from_uri(lulc1_uri)
    cell_size = raster_utils.get_cell_size_from_uri(lulc1_uri)

    #calculate carbon per habitat per cell
    def carbon_per_area_uri_op(value):
        if value == nodata:
            return nodata
        else:
            return sum(carbon_dict[value])

    raster_utils.vectorize_datasets([lulc1_uri],
                                    carbon_per_area_uri_op,
                                    carbon_per_area_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate habitat area per cell
    def area_per_cell_op(value):
        if value == nodata:
            return nodata
        else:
            return cell_size

    raster_utils.vectorize_datasets([lulc1_uri],
                                    area_per_cell_op,
                                    habitat_area_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate carbon per habitat
    def carbon_per_cell_op(value1, value2):
        if (value1 == nodata) or (value2 == nodata):
            return nodata
        else:
            return value1 * value2

    raster_utils.vectorize_datasets([carbon_per_area_uri, habitat_area_uri],
                                    carbon_per_cell_op,
                                    carbon_storage_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #create accumulation raster for t1 to t2

    #construct op from transition matrix
    transition_file = open(transition_matrix_uri)
    #skip header
    header = map(int,transition_file.readline().strip().split(",")[3:])
    #parse table
    transition_dict={}
    for line in transition_file:
        transition = zip([0,0] + header, line.strip().split(","))
        k = transition.pop(0)[1]
        transition.pop(0)
        transition_dict[k] = dict(transition)
    transition_file.close()

    def transition_op(value1, value2):
        if (value1 == nodata) or (value2 == nodata):
            return nodata
        else:
            try:
                return transition_dict[int(value1)][int(value2)]
            except KeyError:
                return 1

    raster_utils.vectorize_datasets([lulc1_uri, lulc2_uri],
                                    transition_op,
                                    transition_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #create carbon storage raster for t2
