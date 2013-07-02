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
    depth_uri = os.path.join(workspace_dir, "depth.tif")

    carbon1_above_uri = os.path.join(workspace_dir, "carbon1_above.tif")
    carbon1_below_uri = os.path.join(workspace_dir, "carbon1_below.tif")
    carbon1_soil_uri = os.path.join(workspace_dir, "carbon1_soil.tif")
    carbon1_litter_uri = os.path.join(workspace_dir, "carbon1_litter.tif")
    carbon1_total_uri = os.path.join(workspace_dir, "carbon1_total.tif")

    transition_uri = os.path.join(workspace_dir, "transition.tif")

    carbon2_above_uri = os.path.join(workspace_dir, "carbon2_above.tif")
    carbon2_below_uri = os.path.join(workspace_dir, "carbon2_below.tif")
    carbon2_soil_uri = os.path.join(workspace_dir, "carbon2_soil.tif")
    carbon2_litter_uri = os.path.join(workspace_dir, "carbon2_litter.tif")
    carbon2_total_uri = os.path.join(workspace_dir, "carbon2_total.tif")
    
    sequestration_uri = os.path.join(workspace_dir, "sequest.tif")

    #accessors
    nodata = raster_utils.get_nodata_from_uri(lulc1_uri)
    cell_size = raster_utils.get_cell_size_from_uri(lulc1_uri)
    cell_area = raster_utils.get_cell_area_from_uri(lulc1_uri)

    assert nodata == raster_utils.get_nodata_from_uri(lulc2_uri)
    assert cell_size == raster_utils.get_cell_size_from_uri(lulc2_uri)
    assert cell_area == raster_utils.get_cell_area_from_uri(lulc2_uri)

    ###create carbon storage raster for t1

    #calculate depth
    def depth_op(value):
        if value == nodata:
            return nodata
        else:
            return 1

    LOGGER.debug("Creating sediment depth raster.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    depth_op,
                                    depth_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #construct dictionary from carbon storage table
    #converts hectares to square meters
    LOGGER.debug("Parsing carbon storage table.")
    carbon_file = open(carbon_uri)
    #skip header
    carbon_file.readline()
    #parse table
    carbon_dict={}
    above_index = 0
    below_index = 1
    soil_index = 2
    litter_index = 3
    for line in carbon_file:
        lulc_code, name, above, below, soil, litter = line.strip().split(",")
        carbon_dict[int(lulc_code)] = [float(above) * cell_area * 1e4,
                                       float(below) * cell_area * 1e4,
                                       float(soil) * cell_area * 1e4,
                                       float(litter) * cell_area * 1e4]
    carbon_file.close()
    

    assert nodata not in carbon_dict

    #construct ops
    #above pool op
    def carbon_above_op(lulc_id):
        if lulc_id == nodata:
            return nodata
        else:
            return carbon_dict[lulc_id][above_index]

    #below pool op
    def carbon_below_op(lulc_id):
        if lulc_id == nodata:
            return nodata
        else:
            return carbon_dict[lulc_id][below_index]

    #soil pool op
    def carbon_soil_op(lulc_id, depth):
        if lulc_id == nodata or depth == nodata:
            return nodata
        else:
            return carbon_dict[lulc_id][soil_index]*depth

    #litter pool op
    def carbon_litter_op(lulc_id):
        if lulc_id == nodata:
            return nodata
        else:
            return carbon_dict[lulc_id][litter_index]

    def carbon_total_op(above, below, soil, litter):
        pixel_stack = [above, below, soil, litter]
        if nodata in pixel_stack:
            return  nodata
        else:
            return sum(pixel_stack)
    
    #calculate rasters
    #calculate above ground carbon pool
    LOGGER.debug("Calculating the above ground carbon pool.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    carbon_above_op,
                                    carbon1_above_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate below ground carbon pool
    LOGGER.debug("Calculating the below ground carbon pool.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    carbon_below_op,
                                    carbon1_below_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate soil carbon pool
    LOGGER.debug("Calculating the soil carbon pool.")
    raster_utils.vectorize_datasets([lulc1_uri, depth_uri],
                                    carbon_soil_op,
                                    carbon1_soil_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate litter carbon pool
    LOGGER.debug("Calculating the litter carbon pool.")
    raster_utils.vectorize_datasets([lulc1_uri],
                                    carbon_litter_op,
                                    carbon1_litter_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate total carbon pool
    LOGGER.debug("Calculating the total carbon pool.")
    raster_utils.vectorize_datasets([carbon1_above_uri, carbon1_below_uri,
                                     carbon1_soil_uri, carbon1_litter_uri],
                                    carbon_total_op,
                                    carbon1_total_uri,
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
