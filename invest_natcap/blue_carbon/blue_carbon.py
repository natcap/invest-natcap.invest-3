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

    return (area_final * carbon_final * depth_final) - \
           (1/((1 + transition_rate) ** year)) * \
           ((area_final * carbon_final * depth_final) - \
            (area_initial * carbon_initial * depth_initial))

def execute(args):
    disturbance_uri = os.path.join(os.path.dirname(__file__),"disturbance.csv")
    disturbance_key_field = "veg type"
    disturbance_loss_name = "%s loss"
    disturbance_depth_name = "%s depth"
    
    
    #preprocess args for possible ease of adoption of future IUI features
    lulc_list = []
    for i in range(1,6):
        if "year_%i" % i in args:
            lulc_list.append({"uri": args["lulc_uri_%i" % i], "year": args["year_%i" % i]})
        else:
            break

    lulc_dict = dict([(lulc["year"], lulc["uri"]) for lulc in lulc_list[1:]])
    lulc_years = lulc_dict.keys()
    lulc_years.sort()

    #carbon stock file names
    above_name = "%i_above.tif"
    below_name = "%i_below.tif"
    soil_name = "%i_soil.tif"
    trans_soil_name = "%i_trans_soil.tif"
    litter_name = "%i_litter.tif"
    biomass_name = "%i_bio.tif"
    carbon_name = "%i_carbon.tif"

    #carbon accumulation file names
    acc_name = "%i_acc.tif"
    soil_acc_name = "%i_soil_acc.tif"
    predisturbance_name = "%i_pre.tif"
    residual_name = "%i_soil_res.tif"
    released_marsh_name = "%i_marsh_rel.tif"
    released_grove_name = "%i_grove_rel.tif"
    released_grass_name = "%i_grass_rel.tif"
    released_other_name = "%i_other_rel.tif"

    disturbed_biomass_marsh_name = "%i_dis_bio_marsh.tif"
    disturbed_biomass_grove_name = "%i_dis_bio_grove.tif"
    disturbed_biomass_grass_name = "%i_dis_bio_grass.tif"
    disturbed_biomass_other_name = "%i_dis_bio_other.tif"

    disturbed_soil_marsh_name = "%i_dis_soil_marsh.tif"
    disturbed_soil_grove_name = "%i_dis_soil_grove.tif"
    disturbed_soil_grass_name = "%i_dis_soil_grass.tif"
    disturbed_soil_other_name = "%i_dis_soil_other.tif"

    #carbon emission and timing file names
    biomass_coefficient_name = "%i_bio_loss.tif"
    soil_coefficient_name = "%i_soil_coefficient.tif"
    magnitude_name = "%i_mag.tif"
    biomass_half_name = "%i_bio_half.tif"
    soil_half_name = "%i_soil_half.tif"
    time_name = "%i_time.tif"

    #constants
    gdal_type = gdal.GDT_Float32
  
    #inputs
    workspace_dir = args["workspace_dir"]
    carbon_uri = args["carbon_pools_uri"]
    carbon_key_field = "ID"
    carbon_veg_field = "Veg Type"
    carbon_above_field = "Above"
    carbon_below_field = "Below"
    carbon_soil_field = "Soil"
    carbon_litter_field = "Litter"
    carbon_depth_field = "Soil Depth"
    carbon_acc_field = "Accum Rate (T CO2e/ha/yr)"

    transition_matrix_uri = args["transition_matrix_uri"]
    transition_key_field = "ID"

    disturbance_biomass_half_life_field = "biomass carbon half life"
    disturbance_soil_half_life_field = "soil carbon half life"

    private_valuation = args["private_valuation"]
    social_valuation = args["social_valuation"]

    disturbance = raster_utils.get_lookup_from_csv(disturbance_uri, disturbance_key_field)
    transition = raster_utils.get_lookup_from_csv(transition_matrix_uri, transition_key_field)
    carbon = raster_utils.get_lookup_from_csv(carbon_uri, carbon_key_field)

    above_dict = dict([(k, carbon[k][carbon_above_field]) for k in carbon])
    below_dict = dict([(k, carbon[k][carbon_below_field]) for k in carbon])
    soil_dict = dict([(k, carbon[k][carbon_soil_field]) for k in carbon])
    litter_dict = dict([(k, carbon[k][carbon_litter_field]) for k in carbon])
    depth_dict = dict([(k, carbon[k][carbon_depth_field]) for k in carbon])
    acc_dict = dict([(k, carbon[k][carbon_acc_field]) for k in carbon])
    biomass_half_dict = dict([(k, disturbance[carbon[k][carbon_veg_field]][disturbance_biomass_half_life_field]) for k in carbon])
    soil_half_dict = dict([(k, disturbance[carbon[k][carbon_veg_field]][disturbance_soil_half_life_field]) for k in carbon])

    #outputs
    depth_uri = os.path.join(workspace_dir, "depth.tif")

    #validating tables
    pass

##    #constructing depth raster
##    LOGGER.info("Creating depth raster.")
##
##    raster_utils.reclassify_dataset_uri(lulc1_uri,
##                               depth_dict,
##                               depth_uri,
##                               gdal_type,
##                               nodata,
##                               exception_flag="values_required")
                
    LOGGER.info("Running analysis.")

    #working on initial year
    lulc_base_year = lulc_list[0]["year"]
    LOGGER.debug("Initial LULC year set to %i.", lulc_base_year)
    lulc_base_uri = lulc_list[0]["uri"]
    LOGGER.debug("Initial LULC set to %s.", lulc_base_uri)

    nodata = raster_utils.get_nodata_from_uri(lulc_base_uri)
    cell_size = raster_utils.get_cell_size_from_uri(lulc_base_uri)

    #reassign nodata values in dictionary to raster nodata values
    for k in biomass_half_dict:
        if (type(biomass_half_dict[k]) == str):
            if (biomass_half_dict[k].lower() == "nodata"):
                biomass_half_dict[k] = nodata
            else:
                msg = "Invalid biomass half life value."
                LOGGER.error(msg)
                raise ValueError, msg

    for k in soil_half_dict:
        if  (type(soil_half_dict[k]) == str):
            if (soil_half_dict[k].lower() == "nodata"):
                soil_half_dict[k] = nodata
            else:
                msg = "Invalid soil hald life value."
                LOGGER.error(msg)
                raise ValueError, msg

    #scale soil carbon by depth
    for k in soil_dict:
        soil_dict[k]=soil_dict[k] * depth_dict[k]

    #vectorize datasets operations            
    def add_op(*values):
        if nodata in values:
            return nodata
        return reduce(operator.add,values)

    def mul_op(*values):
        if nodata in values:
            return nodata
        return reduce(operator.mul,values)    

    def biomass_coefficient_op(original, final):
        if nodata in [original, final]:
            return nodata
        t_value = transition[original][str(int(final))].lower()
        if t_value == "none":
            return 0
        v_value = carbon[original][carbon_veg_field]
        return disturbance[v_value][disturbance_loss_name % t_value]
   
    def soil_coefficient_op(original, final):
        if nodata in [original, final]:
            return nodata
        t_value = transition[original][str(int(final))].lower()
        if t_value == "none":
            return 0
        v_value = carbon[original][carbon_veg_field]
        return disturbance[v_value][disturbance_depth_name % t_value]

    def magnitude_op(biomass_coefficient, biomass, soil_coefficient, soil):
        if nodata in [biomass_coefficient, biomass, soil_coefficient, soil]:
            return nodata
        return (biomass_coefficient * biomass) + (soil_coefficient * soil)    

    #set file paths for lulc base
    lulc_base_above_uri = os.path.join(workspace_dir, above_name % lulc_base_year)
    lulc_base_below_uri = os.path.join(workspace_dir, below_name % lulc_base_year)
    lulc_base_soil_uri = os.path.join(workspace_dir, soil_name % lulc_base_year)
    lulc_base_litter_uri = os.path.join(workspace_dir, litter_name % lulc_base_year)
    lulc_base_biomass_uri = os.path.join(workspace_dir, biomass_name % lulc_base_year)
    lulc_base_carbon_uri = os.path.join(workspace_dir, carbon_name % lulc_base_year)
    lulc_base_acc_uri = os.path.join(workspace_dir, acc_name % lulc_base_year)

    #create base rasters for initial lulc
    LOGGER.info("Creating carbon above pool raster for %i.", lulc_base_year)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               above_dict,
                               lulc_base_above_uri,
                               gdal_type,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon below pool raster for %i.", lulc_base_year)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               below_dict,
                               lulc_base_below_uri,
                               gdal_type,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon soil pool raster for %i.", lulc_base_year)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               soil_dict,
                               lulc_base_soil_uri,
                               gdal_type,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Creating carbon litter pool raster for %i.", lulc_base_year)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               litter_dict,
                               lulc_base_litter_uri,
                               gdal_type,
                               nodata,
                               exception_flag="values_required")

    LOGGER.info("Calculating biomass carbon for %i.", lulc_base_year)
    raster_utils.vectorize_datasets([lulc_base_above_uri, lulc_base_below_uri, lulc_base_litter_uri],
                                    add_op,
                                    lulc_base_biomass_uri,
                                    gdal_type,
                                    nodata,
                                    cell_size,
                                    "union")

    LOGGER.info("Calculating total carbon for %i.", lulc_base_year)
    raster_utils.vectorize_datasets([lulc_base_biomass_uri, lulc_base_soil_uri],
                                    add_op,
                                    lulc_base_carbon_uri,
                                    gdal_type,
                                    nodata,
                                    cell_size,
                                    "union")    

    LOGGER.info("Creating accumulation rate raster for %i.", lulc_base_year)
    raster_utils.reclassify_dataset_uri(lulc_base_uri,
                               acc_dict,
                               lulc_base_acc_uri,
                               gdal_type,
                               nodata,
                               exception_flag="values_required")

    #generate list of snapshot years
    snapshots = [args["analysis_year"]]
    if args["snapshots"]:
        if args["analysis_year"] == "":
            snapshots.extend(range(args["start"],args["analysis_year"]+1,args["step"]))
        else:
            snapshots.extend(range(args["start"],args["stop"]+1,args["step"]))

    analysis_years = list(set(lulc_years+snapshots))
    analysis_years.sort()
    for lulc_transition_year in analysis_years:
        if lulc_transition_year in lulc_years:
            LOGGER.debug("Transition year %i.", lulc_transition_year)
            t = lulc_transition_year - lulc_base_year            
            def timing_op(biomass_half, biomass, soil_half, soil_coefficient, soil):
                if nodata in [biomass_half, biomass_coefficient, biomass, soil_half, soil_coefficient, soil]:
                    return nodata
                return ((0.5 ** (t / biomass_half)) * biomass) + ((0.5 ** (t / soil_half)) * soil_coefficient * soil)

            def accumulation_op(accumulation):
                if nodata in [accumulation]:
                    return nodata
                return accumulation * t
            
            lulc_transition_uri = lulc_dict[lulc_transition_year]

            lulc_base_carbon_accumulation_uri = os.path.join(workspace_dir, soil_acc_name % lulc_base_year)
            lulc_base_soil_residual_uri = os.path.join(workspace_dir, residual_name % lulc_base_year)
            
            lulc_base_biomass_coefficient_uri = os.path.join(workspace_dir, biomass_coefficient_name % lulc_base_year)
            lulc_base_soil_coefficient_uri = os.path.join(workspace_dir, soil_coefficient_name % lulc_base_year)

            lulc_predisturbance_soil_uri = os.path.join(workspace_dir, predisturbance_name % lulc_transition_year)
            
            lulc_base_magnitude_uri = os.path.join(workspace_dir, magnitude_name % lulc_base_year)
            lulc_base_biomass_half_life_uri = os.path.join(workspace_dir, biomass_name % lulc_base_year)
            lulc_base_soil_half_life_uri = os.path.join(workspace_dir, soil_name % lulc_base_year)
            lulc_base_time_uri = os.path.join(workspace_dir, time_name % lulc_base_year)

            #calculate accumulation
            LOGGER.debug("Calculating accumulated soil carbon before disturbance in %i.", lulc_transition_year)
            raster_utils.vectorize_datasets([lulc_base_acc_uri],
                                            accumulation_op,
                                            lulc_base_carbon_accumulation_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

##            LOGGER.debug("Calculating total soil carbon before disturbance in %i.", lulc_transition_year)
##            raster_utils.vectorize_datasets([lulc_base_soil_uri, lulc_base_carbon_accumulation_uri],
##                                            add_op,
##                                            lulc_predisturbance_soil_uri,
##                                            gdal_type,
##                                            nodata,
##                                            cell_size,
##                                            "union")           

            #calculate magnitude and timing of emission
##            LOGGER.debug("Creating biomass disturbance coefficient raster for %i.", lulc_base_year)
##            raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
##                                            biomass_coefficient_op,
##                                            lulc_base_biomass_coefficient_uri,
##                                            gdal_type,
##                                            nodata,
##                                            cell_size,
##                                            "union")

            LOGGER.debug("Creating soil disturbance coefficient raster for %i.", lulc_base_year)
            raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                            soil_coefficient_op,
                                            lulc_base_soil_coefficient_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

            LOGGER.debug("Calculate residual soil carbon after disturbance in %i.", lulc_transition_year)
            raster_utils.vectorize_datasets([lulc_predisturbance_soil_uri, lulc_base_soil_coefficient_uri],
                                            mul_op,
                                            lulc_base_soil_residual_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")            

            LOGGER.debug("Creating biomass half life raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       biomass_half_dict,
                                       lulc_base_biomass_half_life_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")
                
            LOGGER.debug("Creating soil half life raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       soil_half_dict,
                                       lulc_base_soil_half_life_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")
                
            LOGGER.info("Calculating magnitude of loss.")
            raster_utils.vectorize_datasets([lulc_base_biomass_coefficient_uri,
                                             lulc_base_biomass_uri,
                                             lulc_base_soil_coefficient_uri,
                                             lulc_predisturbance_soil_uri],
                                            magnitude_op,
                                            lulc_base_magnitude_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")
            
            LOGGER.info("Calculating primary timing of loss.")
            raster_utils.vectorize_datasets([lulc_base_biomass_half_life_uri,
##                                             lulc_base_biomass_coefficient_uri,
                                             lulc_base_biomass_uri,
                                             lulc_base_soil_half_life_uri,
                                             lulc_base_soil_coefficient_uri,
                                             lulc_predisturbance_soil_uri],
                                            timing_op,
                                            lulc_base_magnitude_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

##            LOGGER.info("Calculating secondary timing of loss.")

            #set base to new LULC and year
            lulc_base_year = lulc_transition_year
            LOGGER.debug("Changed base year to %i." % lulc_base_year)

            lulc_base_uri = lulc_dict[lulc_base_year]            
            LOGGER.debug("Changed base uri to. %s" % lulc_base_uri)

            lulc_base_above_uri = os.path.join(workspace_dir, above_name % lulc_base_year)
            lulc_base_below_uri = os.path.join(workspace_dir, below_name % lulc_base_year)
            lulc_base_trans_soil_uri = os.path.join(workspace_dir, trans_soil_name % lulc_base_year)
            lulc_base_soil_uri = os.path.join(workspace_dir, soil_name % lulc_base_year)
            lulc_base_litter_uri = os.path.join(workspace_dir, litter_name % lulc_base_year)
            lulc_base_biomass_uri = os.path.join(workspace_dir, biomass_name % lulc_base_year)
            lulc_base_carbon_uri = os.path.join(workspace_dir, carbon_name % lulc_base_year)
            lulc_base_acc_uri = os.path.join(workspace_dir, acc_name % lulc_base_year)            

            #create base rasters
            LOGGER.info("Creating carbon above pool raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       above_dict,
                                       lulc_base_above_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")

            LOGGER.info("Creating carbon below pool raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       below_dict,
                                       lulc_base_below_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")

            LOGGER.info("Creating carbon soil pool base raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       soil_dict,
                                       lulc_base_trans_soil_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")

            LOGGER.info("Creating carbon soil pool including residual carbon for %i.", lulc_base_year)
            raster_utils.vectorize_datasets([lulc_base_trans_soil_uri, lulc_base_soil_residual_uri],
                                            add_op,
                                            lulc_base_soil_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

            LOGGER.info("Creating carbon litter pool raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       litter_dict,
                                       lulc_base_litter_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")

            LOGGER.info("Calculating biomass carbon for %i.", lulc_base_year)
            raster_utils.vectorize_datasets([lulc_base_above_uri, lulc_base_below_uri, lulc_base_litter_uri],
                                            add_op,
                                            lulc_base_biomass_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

            LOGGER.info("Calculating total carbon for %i.", lulc_base_year)
            raster_utils.vectorize_datasets([lulc_base_biomass_uri, lulc_base_soil_uri],
                                            add_op,
                                            lulc_base_carbon_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "union")

            LOGGER.info("Creating accumulation rate raster for %i.", lulc_base_year)
            raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                       acc_dict,
                                       lulc_base_acc_uri,
                                       gdal_type,
                                       nodata,
                                       exception_flag="values_required")
                        
##        else:
##            LOGGER.debug("Snapshot year %i.", lulc_transition_year)
##            LOGGER.debug("Calculating accumulation.")
##            LOGGER.debug("Calculating emisson.")

##    for year in range(lulc_list[0]["year"], args["analysis_year"]+1):            
##        if private_valuation:
##            LOGGER.debug("Calculating private valuation.")
##
##        if social_valuation:
##            LOGGER.debug("Calculating social valuation.")
        
    return


##    #inputs
##    workspace_dir = args["workspace_dir"]
##    lulc1_uri = args["lulc1_uri"]
##    year1 = int(args["year1"])
##    lulc2_uri = args["lulc2_uri"]
##    year2 = int(args["year2"])
##    years = year2 - year1
##
##
##
##    if private_valuation:
##        carbon_value = args["carbon_value"]
##        if args["carbon_units"] == "Carbon Dioxide (CO2)":
##            carbon_value *= (15.9994*2+12.0107)/12.0107
##        discount_rate = args["discount_rate"]
##        rate_change = args["rate_change"]
##        private_valuation_uri = os.path.join(workspace_dir, "private_valuation.tif")
##
##
##    if social_valuation:
##        carbon_schedule = args["carbon_schedule"]
##        carbon_schedule_field = args["carbon_schedule_field"]
##        social_valuation_uri = os.path.join(workspace_dir, "social_valuation.tif")
##
##        LOGGER.info("Parsing social cost of carbon table for field %s.", carbon_schedule_field)
##        carbon_schedule_file = open(carbon_schedule)
##        carbon_schedule_index = carbon_schedule_file.readline().split(",").index(carbon_schedule_field)
##        carbon_schedule_dict = {}
##        for line in carbon_schedule_file:
##            row = line.split(",")
##            carbon_schedule_dict[int(row[0])] = float(row[carbon_schedule_index])
##
##        #check schedule for all required years
##        for year in range(year1, year2):
##            if year not in carbon_schedule_dict:
##                msg = "Social cost of carbon missing value for year %i." % year
##                LOGGER.error(msg)
##                raise ValueError, msg
##
##    #intermediate
##    depth_uri = os.path.join(workspace_dir, "depth.tif")
##
##    carbon1_above_uri = os.path.join(workspace_dir, "carbon1_above.tif")
##    carbon1_below_uri = os.path.join(workspace_dir, "carbon1_below.tif")
##    carbon1_soil_uri = os.path.join(workspace_dir, "carbon1_soil.tif")
##    carbon1_litter_uri = os.path.join(workspace_dir, "carbon1_litter.tif")
##
##    transition_uri = os.path.join(workspace_dir, "transition.tif")
##
##    carbon2_above_uri = os.path.join(workspace_dir, "carbon2_above.tif")
##    carbon2_below_uri = os.path.join(workspace_dir, "carbon2_below.tif")
##    carbon2_soil_uri = os.path.join(workspace_dir, "carbon2_soil.tif")
##    carbon2_litter_uri = os.path.join(workspace_dir, "carbon2_litter.tif")
##
##    #outputs
##    carbon1_total_uri = os.path.join(workspace_dir, "carbon1_total.tif")
##    carbon2_total_uri = os.path.join(workspace_dir, "carbon2_total.tif")
##    magnitude_uri = os.path.join(workspace_dir, "magnitude.tif")
##    timing_uri = os.path.join(workspace_dir, "timing.tif")
##    sequestration_uri = os.path.join(workspace_dir, "sequestration.tif")
##
##    #accessors
##    nodata = raster_utils.get_nodata_from_uri(lulc1_uri)
##    cell_size = raster_utils.get_cell_size_from_uri(lulc1_uri)
##    cell_area = raster_utils.get_cell_area_from_uri(lulc1_uri)
##
##    assert nodata == raster_utils.get_nodata_from_uri(lulc2_uri)
##    assert cell_size == raster_utils.get_cell_size_from_uri(lulc2_uri)
##    assert cell_area == raster_utils.get_cell_area_from_uri(lulc2_uri)
##
##    ###create carbon storage raster for t1
##
##    #construct dictionary from carbon storage table
##    #converts hectares to square meters
##    LOGGER.debug("Parsing carbon storage table.")
##    carbon_file = open(carbon_uri)
##    #skip header
##    carbon_file.readline()
##    #parse table
##    emission_dict = {}
##    disturbance_dict = {}
##    soil_life_dict = {}
##    biomass_life_dict = {}
##
##    LOGGER.info("Parsing carbon table.")
##    for line in carbon_file:
##        row = line.strip().split(",")
##        lulc_code = int(row[0])
##        above_dict[lulc_code] = float(row[2]) * cell_area / 1e4
##        below_dict[lulc_code]  = float(row[3]) * cell_area / 1e4
##        soil_dict[lulc_code]  = float(row[4]) * cell_area / 1e4
##        litter_dict[lulc_code]  = float(row[5]) * cell_area / 1e4
##        depth_dict[lulc_code]  = float(row[6])
##        emission_dict[lulc_code] = float(row[7])
##        disturbance_dict[lulc_code] = float(row[8])
##        soil_life_dict[lulc_code] = float(row[9])
##        biomass_life_dict[lulc_code] = float(row[10])
##    carbon_file.close()
##    
##    assert nodata not in above_dict
##
##
##    LOGGER.debug("Creating carbon pool sumation operator.")
##    def carbon_total_op(above, below, soil, litter):
##        pixel_stack = [above, below, soil, litter]
##        if nodata in pixel_stack:
##            return  nodata
##        else:
##            return sum(pixel_stack)
##    
##    LOGGER.info("Creating total carbon pool for time 1.")
##    raster_utils.vectorize_datasets([carbon1_above_uri, carbon1_below_uri,
##                                     carbon1_soil_uri, carbon1_litter_uri],
##                                    carbon_total_op,
##                                    carbon1_total_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##
##    #create accumulation raster for t1 to t2
##
##    #construct op from transition matrix
##    LOGGER.info("Parsing transition table.")
##    transition_file = open(transition_matrix_uri)
##
##    #read header, discard LULC code and name header
##    header = [int(lulc_code) for lulc_code in
##              transition_file.readline().strip().split(",")[3:]]
##    
##    transition_dict={}
##    for line in transition_file:
##        row = line.strip().split(",")
##        #save transition from LULC code
##        k = int(row[0])
##        #build transition to coefficient array, discarding transition from LULC code and name
##        transition_coefficients = [float(coefficient) for coefficient in row[3:]]
##
##        transition_dict[k] = dict(zip(header, transition_coefficients))
##    transition_file.close()
##
##    undefined_transition_set=set([])
##    def transition_op(lulc1, lulc2):
##        if (lulc1 == nodata) or (lulc2 == nodata):
##            return nodata
##        else:
##            try:
##                return transition_dict[int(lulc1)][int(lulc2)]
##            except KeyError:
##                undefined_transition_set.add((int(lulc1), int(lulc2)))
##                return 1
##
##    LOGGER.debug("Creating transition coefficents raster.")
##    raster_utils.vectorize_datasets([lulc1_uri, lulc2_uri],
##                                    transition_op,
##                                    transition_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##
##    for lulc1, lulc2 in undefined_transition_set:
##        LOGGER.warning("Transition from %i to %i undefined and assigned value of 1.", lulc1, lulc2)
##            
##    #soil at time 2 op
##    def soil_transition_op (carbon, coefficient):
##        if (carbon == nodata) or (coefficient == nodata):
##            return nodata
##        else:
##            return carbon * (coefficient ** years)
##
##    #sequestration op
##    def sequestration_op(carbon1, carbon2):
##        if carbon1 == nodata or carbon2 == nodata:
##            return nodata
##        else:
##            return carbon1-carbon2
##
##    LOGGER.info("Creating carbon above pool raster for time 2.")
##    raster_utils.reclassify_dataset_uri(lulc2_uri,
##                               above_dict,
##                               carbon2_above_uri,
##                               gdal_type,
##                               nodata,
##                               exception_flag="values_required")
##
##    LOGGER.info("Creating carbon below pool raster for time 2.")
##    raster_utils.reclassify_dataset_uri(lulc2_uri,
##                               below_dict,
##                               carbon2_below_uri,
##                               gdal_type,
##                               nodata,
##                               exception_flag="values_required")
##
##    #calculate soil carbon pool
##    LOGGER.info("Calculating the soil carbon pool for time 2 based on the transition rate from time 1.")
##    raster_utils.vectorize_datasets([lulc1_uri, transition_uri],
##                                    soil_transition_op,
##                                    carbon2_soil_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##
##    LOGGER.info("Creating carbon litter pool raster for time 2.")
##    raster_utils.reclassify_dataset_uri(lulc2_uri,
##                               litter_dict,
##                               carbon2_litter_uri,
##                               gdal_type,
##                               nodata,
##                               exception_flag="values_required")
##
##    #calculate total carbon pool
##    LOGGER.info("Calculating the total carbon pool for time 2.")
##    raster_utils.vectorize_datasets([carbon2_above_uri, carbon2_below_uri,
##                                     carbon2_soil_uri, carbon2_litter_uri],
##                                    carbon_total_op,
##                                    carbon2_total_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##
##    #calculate net carbon pool
##    LOGGER.debug("Calculating the net carbon pool from time 1 to time 2.")
##    raster_utils.vectorize_datasets([carbon1_total_uri, carbon2_total_uri],
##                                    sequestration_op,
##                                    sequestration_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##
##    ###emission
##
##    #magnitude
##    LOGGER.debug("Creating magnitude operation.")
##    def magnitude_op(lulc_code):
##        if lulc_code == nodata:
##            return nodata
##        else:
##            return (emission_dict[lulc_code]*(above_dict[lulc_code] + below_dict[lulc_code])) +(soil_dict[lulc_code]*disturbance_dict[lulc_code]) + litter_dict[lulc_code]
##
##    LOGGER.info("Calculating magnitude of carbon emission.")
##    raster_utils.vectorize_datasets([lulc1_uri],
##                                    magnitude_op,
##                                    magnitude_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##        
##    #timing
##    LOGGER.debug("Creating timing operation.")
##    def timing_op(lulc_code):
##        if lulc_code == nodata:
##            return nodata
##        else:
##            return ((0.5 ** (years/biomass_life_dict[lulc_code]))*(emission_dict[lulc_code]*(above_dict[lulc_code] + below_dict[lulc_code])) + litter_dict[lulc_code]) + ((0.5 ** (years/soil_life_dict[lulc_code])) * (soil_dict[lulc_code]*disturbance_dict[lulc_code]))
##
##    LOGGER.info("Calculating timing of carbon emission.")
##    raster_utils.vectorize_datasets([lulc1_uri],
##                                    timing_op,
##                                    timing_uri,
##                                    gdal_type,
##                                    nodata,
##                                    cell_size,
##                                    "union")
##    
##
##    ###valuation
##    if private_valuation:
##        LOGGER.debug("Constructing private valuation operation.")
##
##        discount_sum = 1
##        d_rate = 1
##        d_mult = discount_rate / 100.0
##        r_change = 1
##        r_mult = 1 + (rate_change / 100.0)
##
##        for t in range(1,years):
##            d_rate *= d_mult
##            r_change *= r_mult                    
##            discount_sum += d_rate / r_change
##
##        discount_sum = discount_sum * carbon_value
##        def private_valuation_op(sequest):
##            if sequest == nodata:
##                return nodata
##            else:
##                return sequest * discount_sum
## 
##        LOGGER.info("Creating private valuation raster.")
##        raster_utils.vectorize_datasets([sequestration_uri],
##                                        private_valuation_op,
##                                        private_valuation_uri,
##                                        gdal_type,
##                                        nodata,
##                                        cell_size,
##                                        "union")
##
##    if social_valuation:
##        LOGGER.debug("Constructing social cost of carbon operation.")
##        schedule_sum = sum(map(carbon_schedule_dict.__getitem__,range(year1, year2)))        
##        def social_valuation_op(sequest):
##            if sequest == nodata:
##                return nodata
##            else:
##                return sequest * schedule_sum
##
##        LOGGER.info("Creating social valuation raster.")
##        raster_utils.vectorize_datasets([sequestration_uri],
##                                        social_valuation_op,
##                                        social_valuation_uri,
##                                        gdal_type,
##                                        nodata,
##                                        cell_size,
##                                        "union")
