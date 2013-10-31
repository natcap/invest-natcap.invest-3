from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import copy
import os

import operator

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon')

def transition_soil_carbon(area_final, carbon_final, depth_final,
                           transition_rate, year, area_initial,
                           carbon_initial, depth_initial):
    """This is the formula for calculating the transition of soil carbon
    """

    return (area_final * carbon_final * depth_final) - \
           (1/((1 + transition_rate) ** year)) * \
           ((area_final * carbon_final * depth_final) - \
            (area_initial * carbon_initial * depth_initial))

class ConstantOp:
    """A class that allows constants to be added to function calls"""
    def __init__(self, op, *c):
        self.op = op
        self.c = c

    def __call__(self, *f):
        return apply(self.op, f+self.c)

def execute(args):
    ##preprocess args for possible ease of adoption of future IUI features
    #this creates a hypothetical IUI element from existing element
    lulc_list = []
    for i in range(1,6):
        if "year_%i" % i in args:
            lulc_list.append({"uri": args["lulc_uri_%i" % i], "year": args["year_%i" % i]})
        else:
            break

    #create a list of the analysis years and a dictionary of the correspond rasters
    lulc_uri_dict = dict([(lulc["year"], lulc["uri"]) for lulc in lulc_list])
    lulc_years = lulc_uri_dict.keys()
    lulc_years.sort()


    ##constants
    gdal_type = gdal.GDT_Float64


    ##inputs parameters
    workspace_dir = args["workspace_dir"]

    #carbon pools table
    carbon_uri = args["carbon_pools_uri"]

    carbon_field_key = "Id"
    carbon_field_veg = "Veg Type"
    carbon_field_above = "Above"
    carbon_field_below = "Below"
    carbon_field_soil = "Soil"
    carbon_field_litter = "Litter"
    carbon_field_depth = "Soil Depth"

    #transition matrix
    trans_uri = args["transition_matrix_uri"]

    trans_field_key = "Id"

    #disturbance table
    dis_bio_uri = args["biomass_disturbance_csv_uri"]
    dis_soil_uri = args["soil_disturbance_csv_uri"]

    dis_field_key = "veg type"
    dis_field_veg_name = "veg name"

    #accumulation table
    acc_soil_uri = args["accumulation_csv_uri"]

    acc_soil_field_key = "veg type"

    #valuation flags
    private_valuation = args["private_valuation"]
    social_valuation = args["social_valuation"]


    ##outputs
    #carbon pool file names
    above_name = "%i_base_above.tif"
    below_name = "%i_base_below.tif"
    soil_name = "%i_base_soil.tif"
    litter_name = "%i_base_litter.tif"
    biomass_name = "%i_base_biomass.tif"
    carbon_name = "%i_base_total.tif"

    #carbon accumulation file names
    acc_soil_name = "%i_acc_soil.tif"
    acc_soil_co_name = "%i_acc_soil_co.tif"

    #carbon disturbance file names
    dis_bio_co_name = "%i_dis_bio_co.tif"
    dis_soil_co_name = "%i_dis_soil_co.tif"
    dis_bio_name = "%i_dis_bio.tif"
    dis_soil_name = "%i_dis_soil"


    ##process inputs
    #load tables from files
    acc_soil = raster_utils.get_lookup_from_csv(acc_soil_uri, acc_soil_field_key)
    dis_bio = raster_utils.get_lookup_from_csv(dis_bio_uri, dis_field_key)
    dis_soil = raster_utils.get_lookup_from_csv(dis_soil_uri, dis_field_key)
    trans = raster_utils.get_lookup_from_csv(trans_uri, trans_field_key)
    carbon = raster_utils.get_lookup_from_csv(carbon_uri, carbon_field_key)

    #construct dictionaries for single parameter lookups
    above_dict = dict([(k, float(carbon[k][carbon_field_above])) for k in carbon])
    below_dict = dict([(k, float(carbon[k][carbon_field_below])) for k in carbon])
    soil_dict = dict([(k, float(carbon[k][carbon_field_soil])) for k in carbon])
    litter_dict = dict([(k, float(carbon[k][carbon_field_litter])) for k in carbon])
    depth_dict = dict([(k, float(carbon[k][carbon_field_depth])) for k in carbon])

    #validating data
    nodata = set([raster_utils.get_nodata_from_uri(lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(nodata) == 1:
        LOGGER.debug("All rasters have the same nodata value.")
        nodata = nodata.pop()
    else:
        msg = "All rasters must have the same nodata value."
        LOGGER.error(msg)
        raise ValueError, msg

    cell_size = set([raster_utils.get_cell_size_from_uri(lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(cell_size) == 1:
        LOGGER.debug("All masters have the same cell size.")
        cell_size = cell_size.pop()
    else:
        msg = "All rasters must have the same cell size."
        LOGGER.error(msg)
        raise ValueError, msg

    LOGGER.debug("Check for alignment missing...")

    ##vectorize datasets operations
    #standard ops
    def add_op(*values):
        if nodata in values:
            return nodata
        return reduce(operator.add,values)

    def mul_op(*values):
        if nodata in values:
            return nodata
        return reduce(operator.mul,values)

    #custom ops
    def acc_soil_co_op(lulc_base, lulc_transition):
        if nodata in [lulc_base, lulc_transition]:
            return 0.0
        try:
            return float(acc_soil[carbon[int(lulc_base)][carbon_field_veg]]\
                   [trans[int(lulc_base)][str(int(lulc_transition))]])
        except KeyError:
            return 0.0

    def dis_bio_co_op(lulc_base, lulc_transition):
        if nodata in [lulc_base, lulc_transition]:
            return 0.0
        try:
            return float(dis_bio[carbon[int(lulc_base)][carbon_field_veg]]\
                   [trans[int(lulc_base)][str(int(lulc_transition))]])
        except KeyError:
            return 0.0

    def dis_soil_co_op(lulc_base, lulc_transition):
        if nodata in [lulc_base, lulc_transition]:
            return 0.0
        try:
            return float(dis_soil[carbon[int(lulc_base)][carbon_field_veg]]\
                   [trans[int(lulc_base)][str(int(lulc_transition))]])
        except KeyError:
            return 0.0

    LOGGER.debug(acc_soil)
    LOGGER.debug(carbon)
    LOGGER.debug(trans)

    LOGGER.info("Running analysis.")
    ##calculate stock carbon values
    lulc_base_year = lulc_years.pop(0)
    lulc_base_uri = lulc_uri_dict[lulc_base_year]

    LOGGER.info("Calculating stock carbon values.")

    #set file paths for lulc base
    lulc_base_above_uri = os.path.join(workspace_dir, above_name % lulc_base_year)
    lulc_base_below_uri = os.path.join(workspace_dir, below_name % lulc_base_year)
    lulc_base_soil_uri = os.path.join(workspace_dir, soil_name % lulc_base_year)
    lulc_base_litter_uri = os.path.join(workspace_dir, litter_name % lulc_base_year)
    lulc_base_biomass_uri = os.path.join(workspace_dir, biomass_name % lulc_base_year)
    lulc_base_carbon_uri = os.path.join(workspace_dir, carbon_name % lulc_base_year)

    #add reclass entry for nodata
    above_dict[int(nodata)] = 0.0
    below_dict[int(nodata)] = 0.0
    soil_dict[int(nodata)] = 0.0
    litter_dict[int(nodata)] = 0.0
    depth_dict[int(nodata)] = 0.0

    #create base rasters for initial lulc
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               above_dict,
                               lulc_base_above_uri,
                               gdal_type,
                               0.0,
                               exception_flag="values_required")
    LOGGER.debug("Created stock above raster.")

    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               below_dict,
                               lulc_base_below_uri,
                               gdal_type,
                               0.0,
                               exception_flag="values_required")
    LOGGER.debug("Created stock below raster.")

    LOGGER.debug(soil_dict)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               soil_dict,
                               lulc_base_soil_uri,
                               gdal_type,
                               0.0,
                               exception_flag="values_required")
    LOGGER.debug("Created stock soil raster.")

    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               litter_dict,
                               lulc_base_litter_uri,
                               gdal_type,
                               0.0,
                               exception_flag="values_required")
    LOGGER.debug("Created stock litter raster.")

    raster_utils.vectorize_datasets([lulc_base_above_uri, lulc_base_below_uri, lulc_base_litter_uri],
                                    add_op,
                                    lulc_base_biomass_uri,
                                    gdal_type,
                                    0.0,
                                    cell_size,
                                    "union")
    LOGGER.debug("Created stock biomass raster.")

    raster_utils.vectorize_datasets([lulc_base_biomass_uri, lulc_base_soil_uri],
                                    add_op,
                                    lulc_base_carbon_uri,
                                    gdal_type,
                                    0.0,
                                    cell_size,
                                    "union")
    LOGGER.debug("Created stock total raster.")

    ##loop over lulc years
    for lulc_transition_year in lulc_years:
        LOGGER.debug("Transition year %i.", lulc_transition_year)
        lulc_transition_uri = lulc_uri_dict[lulc_transition_year]
        
        t = lulc_transition_year - lulc_base_year

        #local variable names
        lulc_base_acc_soil_co_uri = os.path.join(workspace_dir, acc_soil_co_name % lulc_base_year)
        lulc_base_acc_soil_uri = os.path.join(workspace_dir, acc_soil_name % lulc_base_year)

        lulc_base_dis_bio_co_uri = os.path.join(workspace_dir, dis_bio_co_name % lulc_base_year)
        lulc_base_dis_bio_uri = os.path.join(workspace_dir, dis_bio_name % lulc_base_year)

        lulc_base_dis_soil_co_uri = os.path.join(workspace_dir, dis_soil_co_name % lulc_base_year)
        lulc_base_dis_soil_uri = os.path.join(workspace_dir, dis_soil_name % lulc_base_year)

        ##calculate soil accumulation
        LOGGER.info("Processing soil accumulation.")
        #get coefficients
        try:
            LOGGER.debug(lulc_base_uri)
            LOGGER.debug(lulc_transition_uri)
            raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                            acc_soil_co_op,
                                            lulc_base_acc_soil_co_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")

            LOGGER.debug("Accumulation coefficent raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_acc_soil_co_uri,
                                                  "GTiff",
                                                  0.0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Identity raster for soil accumulation coefficent created.")

        #multiply by number of years
        try:
            raster_utils.vectorize_datasets([lulc_base_acc_soil_co_uri],
                                            ConstantOp(mul_op,t),
                                            lulc_base_acc_soil_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")
            LOGGER.debug("Soil accumulation raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_acc_soil_uri,
                                                  "GTiff",
                                                  0.0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Zero soil accumulation raster created.")

        ##calculate biomass disturbance
        LOGGER.info("Processing biomass disturbance.")
        #get coefficients
        try:
            raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                            biomass_disturbance_co_op,
                                            lulc_base_dis_bio_co_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")

            LOGGER.debug("Biomass disturbance coeffiicent raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_dis_bio_co_uri,
                                                  "GTiff",
                                                  0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Identity raster for biomass disturbance coefficent created.")

        #multiply coefficients by base biomass carbon
        try:
            raster_utils.vectorize_datasets([lulc_base_dis_bio_co_uri, lulc_base_biomass_uri],
                                            mul_op,
                                            lulc_base_dis_bio_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")
            LOGGER.debug("Biomass disturbance raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_dis_bio_uri,
                                                  "GTiff",
                                                  0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Zero biomass disturbance raster created.")

        ##calculate soil disturbance
        LOGGER.info("Processing soil disturbance.")
        try:
            raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                            soil_disturbance_co_op,
                                            lulc_base_dis_soil_co_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")
            LOGGER.debug("Soil disturbance coefficient raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_dis_soil_co_uri,
                                                  "GTiff",
                                                  0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Identity raster for soil disturbance created.")


        #multiply coefficients by base soil carbon
        try:
            raster_utils.vectorize_datasets([lulc_base_dis_soil_co_uri, lulc_base_soil_uri],
                                            mul_op,
                                            lulc_base_dis_soil_uri,
                                            gdal.GDT_Float64,
                                            0.0,
                                            cell_size,
                                            "union")
            LOGGER.debug("Soil disturbance raster created.")

        except:
            raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                  lulc_base_dis_soil_uri,
                                                  "GTiff",
                                                  0,
                                                  gdal.GDT_Byte)
            LOGGER.debug("Zero soil disturbance raster created.")


        #set base to new LULC and year
        lulc_base_year = lulc_transition_year
        LOGGER.debug("Changed base year to %i." % lulc_base_year)

        lulc_base_uri = lulc_uri_dict[lulc_base_year]
        LOGGER.debug("Changed base uri to. %s" % lulc_base_uri)

