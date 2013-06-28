from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import os

def execute(args):
    #inputs
    workspace_dir = args["workspace_dir"]
    lulc_uri = args["lulc_uri"]
    carbon_name = args["carbon_pools_uri"]
    transition_name = args["transition_matrix_uri"]

    #intermediate
    carbon_per_area = os.path.join(workspace_dir, "cpa.tif")
    habitat_area = os.path.join(workspace_dir, "ha.tif")
    carbon_storage = os.path.join(workspace_dir, "cs.tif")

    #construct op from carbon storage table
    carbon_file = open(carbon_name)
    #skip header
    carbon_file.readline()
    #parse table
    carbon_dict={}
    for line in carbon_file:
        lulc_code, name, above, below, soil, litter = line.strip().split(",")
        carbon_dict[int(lulc_code)] = [float(above), float(below),
                                  float(soil), float(litter)]

    #create carbon storage raster for t1
    nodata = raster_utils.get_nodata_from_uri(lulc_uri)
    cell_size = raster_utils.get_cell_size_from_uri(lulc_uri)

    #calculate carbon per habitat per cell
    def carbon_per_area_op(value):
        if value == nodata:
            return nodata
        else:
            return sum(carbon_dict[value])

    raster_utils.vectorize_datasets([lulc_uri],
                                    carbon_per_area_op,
                                    carbon_per_area,
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

    raster_utils.vectorize_datasets([lulc_uri],
                                    area_per_cell_op,
                                    habitat_area,
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

    raster_utils.vectorize_datasets([carbon_per_area, habitat_area],
                                    carbon_per_cell_op,
                                    carbon_storage,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")
                                    
    #create accumulation raster for t1 to t2

    #construct op from transition matrix
    #create carbon storage raster for t2
