from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import copy
import os

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon')

def transition_soil_carbon(area_final, carbon_final, depth_final,
                           transition_rate, year, area_initial,
                           carbon_initial, depth_initial):

    return (area_final * carbon_final * depth_final) - \
           (1/((1 + transition_rate) ** year)) * \
           ((area_final * carbon_final * depth_final) - \
            (area_initial * carbon_initial * depth_initial))

def execute(args):
    #inputs
    workspace_dir = args["workspace_dir"]
    lulc1_uri = args["lulc1_uri"]
    year1 = int(args["year1"])
    lulc2_uri = args["lulc2_uri"]
    year2 = int(args["year2"])
    years = year2 - year1
    carbon_uri = args["carbon_pools_uri"]
    transition_matrix_uri = args["transition_matrix_uri"]

    private_valuation = args["private_valuation"]
    if private_valuation:
        carbon_value = args["carbon_value"]
        if args["carbon_units"] == "Carbon Dioxide (CO2)":
            carbon_value *= (15.9994*2+12.0107)/12.0107
        discount_rate = args["discount_rate"]
        rate_change = args["rate_change"]
        private_valuation_uri = os.path.join(workspace_dir, "private_valuation.tif")

    social_valuation = args["social_valuation"]
    if social_valuation:
        carbon_schedule = args["carbon_schedule"]
        carbon_schedule_field = args["carbon_schedule_field"]
        social_valuation_uri = os.path.join(workspace_dir, "social_valuation.tif")

        LOGGER.info("Parsing social cost of carbon table for field %s.", carbon_schedule_field)
        carbon_schedule_file = open(carbon_schedule)
        carbon_schedule_index = carbon_schedule_file.readline().split(",").index(carbon_schedule_field)
        carbon_schedule_dict = {}
        for line in carbon_schedule_file:
            row = line.split(",")
            carbon_schedule_dict[int(row[0])] = float(row[carbon_schedule_index])

        #check schedule for all required years
        for year in range(year1, year2):
            if year not in carbon_schedule_dict:
                msg = "Social cost of carbon missing value for year %i." % year
                LOGGER.error(msg)
                raise ValueError, msg

    #intermediate
    depth_uri = os.path.join(workspace_dir, "depth.tif")

    carbon1_above_uri = os.path.join(workspace_dir, "carbon1_above.tif")
    carbon1_below_uri = os.path.join(workspace_dir, "carbon1_below.tif")
    carbon1_soil_uri = os.path.join(workspace_dir, "carbon1_soil.tif")
    carbon1_litter_uri = os.path.join(workspace_dir, "carbon1_litter.tif")

    transition_uri = os.path.join(workspace_dir, "transition.tif")

    carbon2_above_uri = os.path.join(workspace_dir, "carbon2_above.tif")
    carbon2_below_uri = os.path.join(workspace_dir, "carbon2_below.tif")
    carbon2_soil_uri = os.path.join(workspace_dir, "carbon2_soil.tif")
    carbon2_litter_uri = os.path.join(workspace_dir, "carbon2_litter.tif")

    #outputs
    carbon1_total_uri = os.path.join(workspace_dir, "carbon1_total.tif")
    carbon2_total_uri = os.path.join(workspace_dir, "carbon2_total.tif")   
    sequestration_uri = os.path.join(workspace_dir, "sequestration.tif")

    #accessors
    nodata = raster_utils.get_nodata_from_uri(lulc1_uri)
    cell_size = raster_utils.get_cell_size_from_uri(lulc1_uri)
    cell_area = raster_utils.get_cell_area_from_uri(lulc1_uri)

    assert nodata == raster_utils.get_nodata_from_uri(lulc2_uri)
    assert cell_size == raster_utils.get_cell_size_from_uri(lulc2_uri)
    assert cell_area == raster_utils.get_cell_area_from_uri(lulc2_uri)

    ###create carbon storage raster for t1

    #construct dictionary from carbon storage table
    #converts hectares to square meters
    LOGGER.debug("Parsing carbon storage table.")
    carbon_file = open(carbon_uri)
    #skip header
    carbon_file.readline()
    #parse table
    above_dict = {}
    below_dict = {}
    soil_dict = {}
    litter_dict = {}
    depth_dict = {}
    emission_dict = {}
    disturbance_dict = {}
    soil_life_dict = {}
    biomass_life_dict = {}

    LOGGER.info("Parsing carbon table.")
    for line in carbon_file:
        row = line.strip().split(",")
        lulc_code = int(row[0])
        above_dict[lulc_code] = float(row[2]) * cell_area * 1e4
        below_dict[lulc_code]  = float(row[3]) * cell_area * 1e4
        soil_dict[lulc_code]  = float(row[4]) * cell_area * 1e4
        litter_dict[lulc_code]  = float(row[5]) * cell_area * 1e4
        depth_dict[lulc_code]  = float(row[6])
        emission_dict[lulc_code] = float(row[7])
        disturbance_dict[lulc_code] = float(row[8])
        soil_life_dict[lulc_code] = float(row[9])
        biomass_life_dict[lulc_code] = float(row[10])
    carbon_file.close()
    
    assert nodata not in above_dict

    LOGGER.info("Creating depth raster.")
    raster_utils.reclassify_dataset_uri(lulc1_uri,
                               depth_dict,
                               depth_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon above pool raster for time 1.")
    raster_utils.reclassify_dataset_uri(lulc1_uri,
                               above_dict,
                               carbon1_above_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon below pool raster for time 1.")
    raster_utils.reclassify_dataset_uri(lulc1_uri,
                               below_dict,
                               carbon1_below_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon soil pool raster for time 1.")
    raster_utils.reclassify_dataset_uri(lulc1_uri,
                               soil_dict,
                               carbon1_soil_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon litter pool raster for time 1.")
    raster_utils.reclassify_dataset_uri(lulc1_uri,
                               litter_dict,
                               carbon1_litter_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.debug("Creating carbon pool sumation operator.")
    def carbon_total_op(above, below, soil, litter):
        pixel_stack = [above, below, soil, litter]
        if nodata in pixel_stack:
            return  nodata
        else:
            return sum(pixel_stack)
    
    LOGGER.info("Creating total carbon pool for time 1.")
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
    LOGGER.info("Parsing transition table.")
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
            return transition_dict[int(lulc1)][int(lulc2)]

    LOGGER.debug("Creating transition coefficents raster.")
    raster_utils.vectorize_datasets([lulc1_uri, lulc2_uri],
                                    transition_op,
                                    transition_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #soil at time 2 op
    def soil_transition_op (carbon, coefficient):
        if (carbon == nodata) or (coefficient == nodata):
            return nodata
        else:
            return carbon * (coefficient ** years)

    #sequestration op
    def sequestration_op(carbon1, carbon2):
        if carbon1 == nodata or carbon2 == nodata:
            return nodata
        else:
            return carbon1-carbon2

    LOGGER.info("Creating carbon above pool raster for time 2.")
    raster_utils.reclassify_dataset_uri(lulc2_uri,
                               above_dict,
                               carbon2_above_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon below pool raster for time 2.")
    raster_utils.reclassify_dataset_uri(lulc2_uri,
                               below_dict,
                               carbon2_below_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    #calculate soil carbon pool
    LOGGER.info("Calculating the soil carbon pool for time 2 based on the transition rate from time 1.")
    raster_utils.vectorize_datasets([lulc1_uri, transition_uri],
                                    soil_transition_op,
                                    carbon2_soil_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    LOGGER.info("Creating carbon litter pool raster for time 2.")
    raster_utils.reclassify_dataset_uri(lulc2_uri,
                               litter_dict,
                               carbon2_litter_uri,
                               gdal.GDT_Float32,
                               nodata,
                               exception_flag="values_required")

    #calculate total carbon pool
    LOGGER.info("Calculating the total carbon pool for time 2.")
    raster_utils.vectorize_datasets([carbon2_above_uri, carbon2_below_uri,
                                     carbon2_soil_uri, carbon2_litter_uri],
                                    carbon_total_op,
                                    carbon2_total_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    #calculate net carbon pool
    LOGGER.debug("Calculating the net carbon pool from time 1 to time 2.")
    raster_utils.vectorize_datasets([carbon1_total_uri, carbon2_total_uri],
                                    sequestration_op,
                                    sequestration_uri,
                                    gdal.GDT_Float32,
                                    nodata,
                                    cell_size,
                                    "union")

    ###valuation
    if private_valuation:
        LOGGER.debug("Constructing private valuation operation.")
        def private_valuation_op(sequest):
            if sequest == nodata:
                return nodata
            else:
                valuation = 0
                for t in range(years):
                    valuation += (sequest * ((discount_rate / 100.0) ** t) * carbon_value) / (1 + (rate_change / 100.0)) ** t
 
            return valuation

        LOGGER.info("Creating private valuation raster.")
        raster_utils.vectorize_datasets([sequestration_uri],
                                        private_valuation_op,
                                        private_valuation_uri,
                                        gdal.GDT_Float32,
                                        nodata,
                                        cell_size,
                                        "union")

    if social_valuation:
        LOGGER.debug("Constructing social cost of carbon operation.")
        def social_valuation_op(sequest):
            if sequest == nodata:
                return nodata
            else:
                valuation = 0
                for year in range(year1, year2):
                    valuation += sequest * carbon_schedule_dict[year]

                return valuation

        LOGGER.info("Creating social valuation raster.")
        raster_utils.vectorize_datasets([sequestration_uri],
                                        social_valuation_op,
                                        social_valuation_uri,
                                        gdal.GDT_Float32,
                                        nodata,
                                        cell_size,
                                        "union")
