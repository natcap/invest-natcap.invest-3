from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import copy
import os

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon')

def execute(args):
    #inputs
    workspace_dir = args["workspace_dir"]
    lulc1_uri = args["lulc1_uri"]
    lulc2_uri = args["lulc2_uri"]
    years = args["years"]
    carbon_uri = args["carbon_pools_uri"]
    transition_matrix_uri = args["transition_matrix_uri"]

    #intermediate
    depth_per_cell_uri = os.path.join(workspace_dir, "d.tif")
    carbon_per_area_uri = os.path.join(workspace_dir, "cpa.tif")
    habitat_area_uri = os.path.join(workspace_dir, "ha.tif")
    carbon_storage_uri = os.path.join(workspace_dir, "cs.tif")
    transition_uri = os.path.join(workspace_dir, "r.tif")
    sequestration_uri = os.path.join(workspace_dir, "s.tif")

    #construct op from carbon storage table
    LOGGER.debug("Parsing carbon storage table.")
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

    #calculate depth
    def depth_per_cell_op(value):
        if value == nodata:
            return nodata
        else:
            return 1

    LOGGER.debug("Creating sediment depth raster.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    depth_per_cell_op,
                                    depth_per_cell_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")
        

    #calculate carbon per habitat per cell
    def carbon_per_area_uri_op(habitat, depth):
        if habitat == nodata:
            return nodata
        else:
            c=copy.copy(carbon_dict[habitat])
            c[2]=c[2]*depth
            return sum(c)

    LOGGER.debug("Calculating carbon per habitat per cell.")
    raster_utils.vectorize_datasets([lulc1_uri, depth_per_cell_uri],
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

    LOGGER.debug("Creating habitat area raster.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    area_per_cell_op,
                                    habitat_area_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate carbon per habitat
    def carbon_per_cell_op(carbon, habitat):
        if (carbon == nodata) or (habitat == nodata):
            return nodata
        else:
            return carbon * habitat

    LOGGER.debug("Creating carbon storage raster.")
    raster_utils.vectorize_datasets([carbon_per_area_uri, habitat_area_uri],
                                    carbon_per_cell_op,
                                    carbon_storage_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #create accumulation raster for t1 to t2

    #construct op from transition matrix
    LOGGER.debug("Parsing transition matrix.")
    transition_file = open(transition_matrix_uri)

    #read header, discard LULC code and name header
    header = [int(lulc_code) for lulc_code in
              transition_file.readline().strip().split(",")[3:]]
    
    transition_dict={}
    for line in transition_file:
        row = line.strip().split(",")
        #save transition from LULC code
        k = int(row[0])
        #build transition to coefficient array, discarding transition from LULC code and name
        transition_coefficients = [float(coefficient) for coefficient in row[3:]]

        transition_dict[k] = dict(zip(header, transition_coefficients))
    transition_file.close()

    def transition_op(lulc1, lulc2):
        if (lulc1 == nodata) or (lulc2 == nodata):
            return nodata
        else:
            try:
                return transition_dict[int(lulc1)][int(lulc2)]
            except KeyError:
                return 1

    LOGGER.debug("Creating transition coefficents raster.")
    raster_utils.vectorize_datasets([lulc1_uri, lulc2_uri],
                                    transition_op,
                                    transition_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #construct op for compounding sequestration
    def sequestration_op (carbon, coefficient):
        if (carbon == nodata) or (coefficient == nodata):
            return nodata
        else:
            return carbon * (coefficient ** years)

    #create carbon storage raster for t2
    LOGGER.debug("Creating carbon storage at time 2 raster.")
    raster_utils.vectorize_datasets([carbon_storage_uri, transition_uri],
                                    sequestration_op,
                                    sequestration_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")
