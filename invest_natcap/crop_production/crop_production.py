import crop_production_core
import logging

import os

from osgeo import gdal, ogr, osr
#gdal.UseExceptions()

from invest_natcap import raster_utils

import json

import operator

import numpy

import sys

import random

import math

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('crop_production')

logging.getLogger("root").setLevel(logging.WARNING)
logging.getLogger("raster_utils").setLevel(logging.WARNING)
logging.getLogger("raster_cython_utils").setLevel(logging.WARNING)

        
def execute(args):
    config_uri = os.path.join(os.path.dirname(__file__), "config.json")
    LOGGER.debug("Loading configuration file: %s", config_uri)
    config = json.loads(open(config_uri).read())
  
    gdal_type_cover = gdal.GDT_Int32
    gdal_type_float = gdal.GDT_Float32
    nodata_int = -1
    nodata_float = -1.0

    table_precision = 2

    intermediate_dir = "intermediate"

    reclass_name = "crop_reclass.tif"

    report_name = "report.htm"

##    use_existing_crops = args["enable_tab_existing"]
##    use_percentile_crops = args["enable_tab_percentile"]
##    use_modeled_crops = args["enable_tab_modeled"]
##
##    if not any([use_existing_crops,
##                use_percentile_crops,
##                use_modeled_crops]):
##        LOGGER.error("You must select at least one crop yield method.")
##        raise ValueError, "You must select at least one crop yield method."
        

    workspace_dir = args["workspace_dir"]

    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)

    crop_cover_uri = args["crop_file_name"]

    reclass_table_uri = args["reclass_table"]
    reclass_table_field_key = "Input Value"
    reclass_table_field_invest = "InVEST Value"

    raster_table_uri = args["raster_table"]
    raster_path = os.path.dirname(raster_table_uri)
    raster_table_field_key = "Id"
    raster_table_field_short_name = "Crop"
    raster_table_other_short_name = "Other"

    raster_table_field_K2O = "K2O_apprate"
    raster_table_field_N = "N_apprate"
    raster_table_field_P2O5 = "P2O5_apprate"

    raster_table_field_yield = "yield"
    raster_table_field_area = "harea"

    raster_table_field_climate = "Climate"

    crop_yield_name = "%i_yield_masked.tif"
    clip_yield_name = "%i_yield_clip.tif"
    projected_yield_name = "%i_yield_prj.tif"

    crop_area_name = "%i_area_masked.tif"
    clip_area_name = "%i_area_clip.tif"
    projected_area_name = "%i_area_prj.tif"

    crop_production_name = "%i_prod.tif"

    yield_percentile_name = "yield_percentile_%i.tif"

    intermediate_uri = os.path.join(workspace_dir, intermediate_dir)

    if not os.path.exists(os.path.join(workspace_dir, intermediate_dir)):
        os.makedirs(os.path.join(workspace_dir, intermediate_dir))

    reclass_crop_cover_uri = os.path.join(intermediate_uri,
                                          reclass_name)

    report_uri = os.path.join(workspace_dir, report_name)

    nutrient_100g_name = "nutrient_100g_%s.tif"

    valuation_table_field_subregion = "Subregion"

    subregion_uri = args["valuation_raster"]
    subregion_clip_name = "subregion_clip.tif"
    subregion_project_name = "subregion_project.tif"
    subregion_align_name = "subregion_align.tif"
    subregion_name = "subregion.tif"

    field_returns = "Return"
    field_irrigation = "Irrigation"
    field_fertilizer = "Fertilizer"

    fertilizer_name = "%i_%s.tif"
    fertilizer_prj_name = "%i_%s_prj.tif"
    fertilizer_cost_name = "%i_%s_cost.tif"

    nutrient_name = "nutrient_%s.tif"

    extent_name = "extent.shp"
    extent_4326_name = "extent_4326.shp"
    sr_4326 = osr.SpatialReference()
    sr_4326.ImportFromEPSG(4326)
    wkt = sr_4326.ExportToWkt()
    extent_uri = os.path.join(intermediate_uri, extent_name)
    extent_4326_uri = os.path.join(intermediate_uri, extent_4326_name)

    output_wkt = raster_utils.get_dataset_projection_wkt_uri(crop_cover_uri)

    crop_production_core.datasource_from_dataset_bounding_box_uri(crop_cover_uri, extent_uri)

    raster_utils.reproject_datasource_uri(extent_uri, wkt, extent_4326_uri)
         
    nodata_name = os.path.join(intermediate_uri, "nodata_%i.tif")

    #data validation and setup
    if not os.path.exists(intermediate_uri):
        os.makedirs(intermediate_uri)

    LOGGER.debug("Raster path: %s.", raster_path)

    cell_size = raster_utils.get_cell_size_from_uri(crop_cover_uri)
    LOGGER.debug("Crop cover cell size %s square meters.", cell_size)

    #raster table
    raster_table_csv_dict = raster_utils.get_lookup_from_csv(raster_table_uri,
                                                             raster_table_field_key)

    if 0 in raster_table_csv_dict:
        raise ValueError, "There should not be an entry in the raster table for cover 0."

    raster_table_csv_dict[0] = {raster_table_field_short_name: raster_table_other_short_name}

    #reclass crop cover
    reclass_table_csv_dict = raster_utils.get_lookup_from_csv(reclass_table_uri,
                                                              reclass_table_field_key)

    reclass_table = {}
    for crop in reclass_table_csv_dict:
        reclass_table[crop] = reclass_table_csv_dict[crop][reclass_table_field_invest]

    reclass_table[0] = 0

    raster_utils.reclassify_dataset_uri(crop_cover_uri,
                                        reclass_table,
                                        reclass_crop_cover_uri,
                                        gdal_type_cover,
                                        nodata_int,
                                        exception_flag = "values_required",
                                        assert_dataset_projected = False)

    invest_crop_counts = raster_utils.unique_raster_values_count(reclass_crop_cover_uri)
    invest_crops = invest_crop_counts.keys()
    invest_crops.sort()
    if invest_crops[0] == 0:
        invest_crops.pop(0)

    #create valuation rasters if needed
        
    if args["calculate_valuation"]:
        nitrogen_name = "nitrogen.tif"
        nitrogen_cost_rate_name = "nitrogen_cost_rate.tif"
        nitrogen_cost_name = "nitrogen_cost.tif"

        phosphorus_name = "phosphorus.tif"
        phosphorus_cost_rate_name = "phosphorus_cost_rate.tif"
        phosphorus_cost_name = "phosphorus_cost.tif"

        potassium_name = "potassium.tif"
        potassium_cost_rate_name = "potassium_cost_rate.tif"
        potassium_cost_name = "potassium_cost.tif"

        irrigation_name = "irrigation.tif"

        labor_name = "labor_cost_rate.tif"
        machine_name = "machine_cost_rate.tif"
        seed_name = "seed_cost_rate.tif"

        crop_cost_name = "crop_cost.tif"

        valuation_field_N_cost = "avg_N"
        valuation_field_P_cost = "avg_P"
        valuation_field_K_cost = "avg_K"
        valuation_field_labor_cost = "laborcost"

        intermediate_nitrogen_clip_name = "crop_%i_N_clip.tif"
        intermediate_nitrogen_clip_prj_name = "crop_%i_N_clip_prj.tif"

        try:
            valuation_field_machine_cost = args["field_machine"]
        except KeyError:
            pass

        try:
            valuation_field_seed_cost = "actual_seed"
        except KeyError:
            pass
        
        valuation_field_crop_cost = "avgPP"


        valuation_csv_uri = args["valuation_table"]
        valuation_field_id = "Id"
        valuation_csv_dict = raster_utils.get_lookup_from_csv(valuation_csv_uri,
                                                              valuation_field_id)

        ##subregion identification
        LOGGER.debug("Determining geographic subregion(s).")
        subregion_clip_uri = raster_utils.temporary_filename() #os.path.join(intermediate_uri, subregion_clip_name)
        subregion_project_uri = raster_utils.temporary_filename() #os.path.join(intermediate_uri, subregion_project_name)
        subregion_align_uri = os.path.join(intermediate_uri, subregion_name) #subregion_align_name)
        

        #clip
        raster_utils.clip_dataset_uri(subregion_uri,
                                      extent_4326_uri,
                                      subregion_clip_uri,
                                      assert_projections=False)
        #project
        raster_utils.warp_reproject_dataset_uri(subregion_clip_uri,
                                                cell_size,
                                                output_wkt,
                                                "nearest",
                                                subregion_project_uri)

        #align
        raster_utils.align_dataset_list([reclass_crop_cover_uri,
                                         subregion_project_uri],
                                        [raster_utils.temporary_filename(),
                                         subregion_align_uri],
                                        ["nearest", "nearest"],
                                        cell_size,
                                        "dataset",
                                        0,
                                        dataset_to_bound_index=0)

        
        ##generate fertilizer rasters if necessary
        #nitrogen
        if args["valuation_override_quantities"] and args["nitrogen_uri"]!= "":
            nitrogen_uri = args["nitrogen_uri"]            
        else:
            LOGGER.debug("Creating nitrogen fertilizer raster.")
            nitrogen_uri = os.path.join(intermediate_uri, nitrogen_name)

            crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                              invest_crops,
                              cell_size,
                              output_wkt,
                              raster_table_csv_dict,
                              raster_table_field_N,
                              raster_path,
                              extent_4326_uri,
                              nitrogen_uri)

        LOGGER.debug("Creating nitrogen fertilizer cost rate raster.")
        nitrogen_cost_rate_uri = os.path.join(intermediate_uri, nitrogen_cost_rate_name)

        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                         subregion_align_uri],
                                        crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                               valuation_field_N_cost,
                                                               nodata_float),
                                        nitrogen_cost_rate_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0,
                                        dataset_to_align_index=0)

        LOGGER.debug("Creating nitrogen fertilizer cost raster.")
        nitrogen_cost_uri = os.path.join(intermediate_uri, nitrogen_cost_name)

        raster_utils.vectorize_datasets([nitrogen_uri, nitrogen_cost_rate_uri],
                                        crop_production_core.mul_closure([nodata_float, nodata_float], nodata_float),
                                        nitrogen_cost_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0)
                                        
        #phosphorus            
        if args["valuation_override_quantities"] and args["phosphorus_uri"] != "":
            phosphorus_uri = args["phosphorus_uri"]
        else:
            LOGGER.debug("Creating phosphorus raster.")
            phosphorus_uri = os.path.join(intermediate_uri, phosphorus_name)

            crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                              invest_crops,
                              cell_size,
                              output_wkt,
                              raster_table_csv_dict,
                              raster_table_field_P2O5,
                              raster_path,
                              extent_4326_uri,
                              phosphorus_uri)

        LOGGER.debug("Creating phosphorus fertilizer cost rate raster.")
        phosphorus_cost_rate_uri = os.path.join(intermediate_uri, phosphorus_cost_rate_name)

        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                         subregion_align_uri],
                                        crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                               valuation_field_P_cost,
                                                               nodata_float),
                                        phosphorus_cost_rate_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0,
                                        dataset_to_align_index=0)

        LOGGER.debug("Creating phosphorus fertilizer cost raster.")
        phosphorus_cost_uri = os.path.join(intermediate_uri, phosphorus_cost_name)

        raster_utils.vectorize_datasets([phosphorus_uri, phosphorus_cost_rate_uri],
                                        crop_production_core.mul_closure([nodata_float, nodata_float], nodata_float),
                                        phosphorus_cost_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0)

        #potassium
        if args["valuation_override_quantities"] and args["potassium_uri"] != "":
            potassium_uri = args["potassium_uri"]
        else:
            LOGGER.debug("Creating potassium raster.")
            potassium_uri = os.path.join(intermediate_uri, potassium_name)

            crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                              invest_crops,
                              cell_size,
                              output_wkt,
                              raster_table_csv_dict,
                              raster_table_field_K2O,
                              raster_path,
                              extent_4326_uri,
                              potassium_uri)

        LOGGER.debug("Creating potassium fertilizer cost rate raster.")
        potassium_cost_rate_uri = os.path.join(intermediate_uri, potassium_cost_rate_name)

        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                         subregion_align_uri],
                                        crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                               valuation_field_K_cost,
                                                               nodata_float),
                                        potassium_cost_rate_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0,
                                        dataset_to_align_index=0)

        LOGGER.debug("Creating potassium fertilizer cost raster.")
        potassium_cost_uri = os.path.join(intermediate_uri, potassium_cost_name)

        raster_utils.vectorize_datasets([potassium_uri, potassium_cost_rate_uri],
                                        crop_production_core.mul_closure([nodata_float, nodata_float], nodata_float),
                                        potassium_cost_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0)

        ##labor raster
        if args["valuation_override_prices"] and args["labor_uri"] != "":
            labor_uri = args["labor_uri"]
        else:
            LOGGER.debug("Creating labor raster.")
            labor_uri = os.path.join(intermediate_uri, labor_name)

            raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                             subregion_align_uri],
                                            crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                                   valuation_field_labor_cost,
                                                                   nodata_float),
                                            labor_uri,
                                            gdal_type_float,
                                            nodata_float,
                                            cell_size,
                                            "dataset",
                                            dataset_to_bound_index=0,
                                            dataset_to_align_index=0)

        ##machine raster            
        if args["valuation_override_prices"] and args["machine_uri"] != "":
            machine_uri = args["machine_uri"]
        else:
            LOGGER.debug("Creating %s machine raster.", valuation_field_machine_cost)
            machine_uri = os.path.join(intermediate_uri, machine_name)

            raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                             subregion_align_uri],
                                            crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                                   valuation_field_machine_cost,
                                                                   nodata_float),
                                            machine_uri,
                                            gdal_type_float,
                                            nodata_float,
                                            cell_size,
                                            "dataset",
                                            dataset_to_bound_index=0,
                                            dataset_to_align_index=0)

        ##seed raster            
        if args["valuation_override_prices"] and args["seed_uri"] != "":
            seed_uri = args["seed_uri"]
        else:
            LOGGER.debug("Creating %s seed raster.", valuation_field_machine_cost)
            seed_uri = os.path.join(intermediate_uri, seed_name)

            raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                             subregion_align_uri],
                                            crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                                   valuation_field_seed_cost,
                                                                   nodata_float),
                                            seed_uri,
                                            gdal_type_float,
                                            nodata_float,
                                            cell_size,
                                            "dataset",
                                            dataset_to_bound_index=0,
                                            dataset_to_align_index=0)

        LOGGER.debug("Creating %s crop cost raster.", valuation_field_crop_cost)
        crop_cost_uri = os.path.join(intermediate_uri, crop_cost_name)
        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                         subregion_align_uri],
                                        crop_production_core.lookup_reclass_closure(valuation_csv_dict,
                                                               valuation_field_crop_cost,
                                                               nodata_float),
                                        crop_cost_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0,
                                        dataset_to_align_index=0)



        if args["calculate_nutrition"]:
            def reclass_no_keyerror_closure(d, keyerror_value):
                def reclass_no_keyerror_op(k):
                    try:
                        return d[k]
                    except KeyError:
                        return keyerror_value

                return reclass_no_keyerror_op
                    
            #load nutrition table
            nutrition_table_dict = raster_utils.get_lookup_from_csv(args["nutrition_table"],
                                                                    config["nutrition_table"]["id_field"])
            #construct dictionary for included nutrients
            nutrient_selection = {}
            nutrient_aliases = {}
            for nutrient in config["nutrition_table"]["columns"]:
                args_id = config["nutrition_table"]["columns"][nutrient]["args_id"]
                if args_id in args:
                    LOGGER.info("Including nutrient %s in analysis.", nutrient)
                    if args[args_id] == "":
                        nutrient_100g_uri = os.path.join(intermediate_uri, nutrient_100g_name % nutrient)
                        
                        LOGGER.debug("Nutrient %s will be determined by nutrition CSV.", nutrient)
                        nutrient_selection[nutrient] = True
                        nutrient_aliases[nutrient] = config["nutrition_table"]["columns"][nutrient]["formatting"]["abbreviation"]

                        reclass_table = dict([(k,
                                               nutrition_table_dict[k][nutrient]) for k in nutrition_table_dict.keys()])
                        reclass_table[0] = 0.0

                        nutrient_uri = os.path.join(intermediate_uri, nutrient_name % nutrient_aliases[nutrient])

                        raster_utils.vectorize_datasets([reclass_crop_cover_uri],
                                                        reclass_no_keyerror_closure(reclass_table, nodata_float),
                                                        nutrient_uri,
                                                        gdal_type_float,
                                                        nodata_float,
                                                        cell_size,
                                                        "dataset",
                                                        dataset_to_bound_index=0,
                                                        dataset_to_align_index=0)
                        
                    else:
                        uri = args[args_id]
                        LOGGER.info("Overriding nutrient %s table values with raster %s.", nutrient, uri)

            for nutrient in nutrient_selection:
                LOGGER.debug("Creating %s nutrient raster.", nutrient)
             
##            calculate_nutrition(reclass_crop_cover_uri,
##                                yield_type,
##                                nutrition_table_dict,
##                                nutrient_selection,
##                                intermediate_uri,
##                                nutrient_name,
##                                invest_crops,
##                                nutrient_aliases)


    LOGGER.info("Calculating existing yield.")

    yield_uri = os.path.join(intermediate_uri, "yield_existing.tif")
    
    crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                      invest_crops,
                      cell_size,
                      output_wkt,
                      raster_table_csv_dict,
                      raster_table_field_yield,
                      raster_path,
                      extent_4326_uri,
                      yield_uri)

    area_uri = os.path.join(intermediate_uri, "harea_existing.tif")
    crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                      invest_crops,
                      cell_size,
                      output_wkt,
                      raster_table_csv_dict,
                      raster_table_field_area,
                      raster_path,
                      extent_4326_uri,
                      area_uri)

    LOGGER.info("Calulating percentile yield.")
    climate_uri = os.path.join(intermediate_uri, "climate.tif")

    crop_production_core.mosaic_by_attribute_uri(reclass_crop_cover_uri,
                      invest_crops,
                      cell_size,
                      output_wkt,
                      raster_table_csv_dict,
                      raster_table_field_climate,
                      raster_path,
                      extent_4326_uri,
                      climate_uri)
    
    


##    LOGGER.debug("Creating income raster.")
##    income_uri = os.path.join(intermediate_uri, "income.tif")
##
##    clip_project_align_dataset_uri(args["income_raster"], reclass_crop_cover_uri, income_uri)

    def percentile_yield_closer(reclass_crop_cover_uri,
                                climate_uri,
                                income_uri,
                                file_index_uri,
                                raster_path,
                                file_index_field_key,
                                file_index_field_percentile,
                                percentile_field_key,
                                percentile,
                                default_value = 0,
                                nodata = -1,
                                ignore_crop=None):

        file_index = raster_utils.get_lookup_from_csv(file_index_uri, file_index_field_key)
        crop_types = list(raster_utils.unique_raster_values_count(reclass_crop_cover_uri).keys())

        if ignore_crop != None:
            try:
                crop_types = set(crop_types)
                crop_types.remove(ignore_crop)
            except KeyError:
                LOGGER.warning("Ignore crop %i not present.", ignore_crop)
            crop_types = list(crop_types)
            
        yield_dict = {}
        for crop in crop_types:
            csv_uri = file_index[crop][file_index_field_percentile]
            if csv_uri != "":
                csv_uri = os.path.join(raster_path, csv_uri)
                LOGGER.debug("Processing: %s", csv_uri)
                yield_dict[crop] = raster_utils.get_lookup_from_csv(csv_uri,
                                                                    percentile_field_key)
            else:
                yield_dict[crop] = NoKeyErrorDict({}, nodata)

        incomes = ["Nodata", "HiIncome%i", "MedIncome%i", "LowIncome%i", "AllIncome%i"]

        nodata_list = [raster_utils.get_nodata_from_uri(raster) for raster in [reclass_crop_cover_uri,
                                                                                climate_uri,
                                                                                income_uri]]
        def percentile_yield_op(crop, climate, income):
            #print crop, climate, income
            if any([apply(operator.eq, pair) for pair in zip([crop, climate, income], nodata_list)]):
                return nodata
            elif ignore_crop != None and crop == ignore_crop:
                return default_value
            elif income == 0 or climate == 0:
                return nodata
            else:
                try:
                    return float(yield_dict[int(crop)][int(climate)][incomes[int(income)] % percentile])
                except ValueError:
                    try:
                        return float(yield_dict[crop][climate][incomes[4] % percentile])
                    except ValueError:
                        return default_value

        return percentile_yield_op

##    for percentile in [25, 50, 75, 95]:
##        LOGGER.debug("Creating yield using %i percent.", percentile)
##        yield_uri = os.path.join(intermediate_uri, yield_percentile_name % percentile)
##
##        percentile_yield_op = percentile_yield_closer(reclass_crop_cover_uri,
##                                                      climate_uri,
##                                                      income_uri,
##                                                      raster_table_uri,
##                                                      raster_path,
##                                                      raster_table_field_key,
##                                                      "CBI_yield",
##                                                      "ClimateBin",
##                                                      percentile,
##                                                      default_value = 0,
##                                                      nodata = -1,
##                                                      ignore_crop = 0)
##
##        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
##                                         climate_uri,
##                                         income_uri],
##                                        percentile_yield_op,
##                                        yield_uri,
##                                        gdal_type_float,
##                                        nodata_float,
##                                        cell_size,
##                                        "dataset",
##                                        dataset_to_bound_index=0,
##                                        dataset_to_align_index=0)                                        
##                                                      


##    if args["enable_tab_modeled"]:
####        LOGGER.debug("Testing file.")
####
####        uri = "/home/mlacayo/workspace/CropProduction/input/yield_mod/wheat_m3yieldmodeldata_VL_MBM.csv"
####        test = raster_utils.get_lookup_from_csv(uri,
####                                                "climate bin")
####
####        return
##        LOGGER.info("Calculating modeled yield.")
##
##
##        file_field_yield_mod = "Yield_mod"
##        
##        modeled_field_key = "climate bin"
##        modeled_field_y_max = "yield ceiling"
##        modeled_field_b_NP = "b_nut"
##        modeled_field_b_K = "b_K2O"
##        modeled_field_C_N = "c_N"
##        modeled_field_C_P = "c_P2O5"
##        modeled_field_C_K = "c_K2O"
##        #modeled_field_N_GC = "N_apprate"
##        #modeled_field_P_GC = "P_apprate"
##        #modeled_field_K_GC = "K_apprate"
##
##        def modeled_closure(crop_uri,
##                            file_index_uri,
##                            file_index_field_key,
##                            nodata = -1,
##                            ignore_crop = 0):
##
##            LOGGER.debug("Building modeled_op.")
##
##            file_index = raster_utils.get_lookup_from_csv(file_index_uri, file_index_field_key)
##            crop_types = list(raster_utils.unique_raster_values_count(crop_uri).keys())
##
##            crop_nodata = raster_utils.get_nodata_from_uri(crop_uri)
##
##            if ignore_crop != None:
##                try:
##                    crop_types = set(crop_types)
##                    crop_types.remove(ignore_crop)
##                except KeyError:
##                    LOGGER.warning("Ignore crop %i not present.", ignore_crop)
##                crop_types = list(crop_types)
##
##            modeled_dict = {}
##            required_keys_set = set([modeled_field_key,
##                                     modeled_field_y_max,
##                                     modeled_field_b_NP,
##                                     modeled_field_b_K,
##                                     modeled_field_C_N,
##                                     modeled_field_C_P,
##                                     modeled_field_C_K])
##
##            LOGGER.debug("Parsing climate bin model CSVs.")
##            for crop in crop_types:
##                csv_uri = file_index[crop][file_field_yield_mod]
##                if csv_uri != "":
##                    csv_uri = os.path.join(raster_path, csv_uri)
##                    LOGGER.debug("Processing: %s", csv_uri)
##
##                    modeled_dict[crop] = raster_utils.get_lookup_from_csv(csv_uri,
##                                                                          modeled_field_key)
##
##                    provided_keys_set = set(modeled_dict[crop][random.choice(modeled_dict[crop].keys())])
##                    missing_keys_set = required_keys_set.difference(provided_keys_set)
##
##                    if missing_keys_set != set([]):
##                        msg = "%s does not contain the following required keys: %s." % (csv_uri, str(missing_keys_set))
##                        LOGGER.error(msg)
##                        raise KeyError, msg
##                            
##                else:
##                    modeled_dict[crop] = None
##
##            LOGGER.debug("Defining modeled_op.")
##
##            
##            def modeled_op(crop, climate, N, P, K):
##                if crop == ignore_crop or (crop_nodata in [crop, climate, N, P, K]) or modeled_dict[int(crop)] == None:
##                    return nodata
##                else:
##                    y_max = modeled_dict[int(crop)][int(climate)][modeled_field_y_max]
##                    b_NP = modeled_dict[int(crop)][int(climate)][modeled_field_b_NP]
##                    b_K = modeled_dict[int(crop)][int(climate)][modeled_field_b_K]
##                    C_N = modeled_dict[int(crop)][int(climate)][modeled_field_C_N]
##                    C_P = modeled_dict[int(crop)][int(climate)][modeled_field_C_P]
##                    C_K = modeled_dict[int(crop)][int(climate)][modeled_field_C_K]
##                    
##                    try:
##                        N_yield = y_max * (1 - (b_NP * math.exp(-1 * C_N * N)))
##                        P_yield = y_max * (1 - (b_NP * math.exp(-1 * C_P * P)))
##                        K_yield = y_max * (1 - (b_NP * math.exp(-1 * C_K * K)))
##                    except TypeError:
##                        return 0
##
##                    return min([N_yield, P_yield, K_yield])
##
##            LOGGER.debug("Completed building modeled_op.")
##
##            return modeled_op
##
##        yield_uri = os.path.join(intermediate_uri, "yield_modeled.tif")
##
##        modeled_op = modeled_closure(reclass_crop_cover_uri,
##                                     raster_table_uri,
##                                     raster_table_field_key)
##        
##        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
##                                         climate_uri,
##                                         nitrogen_uri,
##                                         phosphorus_uri,
##                                         potassium_uri],
##                                        modeled_op,
##                                        yield_uri,
##                                        gdal_type_float,
##                                        nodata_float,
##                                        cell_size,
##                                        "dataset",
##                                        dataset_to_bound_index=0,
##                                        dataset_to_align_index=0)

    return

    projected=True

    #calculate existing yields
    yield_list = []
    if args["enable_tab_existing"]:

        calculate_production_existing(reclass_crop_cover_uri,
                                      raster_table_csv_dict,
                                      raster_path,
                                      raster_table_field_yield,
                                      raster_table_field_area,
                                      extent_4326_uri,
                                      intermediate_uri,
                                      clip_yield_name,
                                      projected_yield_name,
                                      crop_yield_name,
                                      clip_area_name,
                                      projected_area_name,
                                      crop_area_name,
                                      crop_production_name,
                                      cell_size,
                                      output_wkt,
                                      gdal_type_float,
                                      nodata_float,                                  
                                      invest_crops,
                                      projected)

        yield_list.append(())

    #generate report tables
    for label, uri in yield_list:

        #summarize yield

        if args["calculate_valuation"]:
            LOGGER.debug("Calculating valuation.")

            gdal_type=gdal.GDT_Float32
            nodata = -1
            cell_size = None
            calculate_valuation(crop_uri,
                                intensity_uri,
                                subregion_project_uri,
                                nitrogen_uri,
                                phosphorus_uri,
                                potassium_uri,
                                irrigation_uri,
                                labor_uri,
                                machine_uri,
                                seed_uri,
                                valuation_dict,
                                field_nitrogen,
                                field_phophorus,
                                field_potassium,
                                field_irrigation,
                                field_labor,
                                field_machine,
                                field_seed,
                                nitrogen_cost_uri,
                                phosphorus_cost_uri,
                                potassium_cost_uri,
                                irrigation_cost_uri,
                                labor_cost_uri,
                                machine_cost_uri,
                                seed_cost_uri,
                                gdal_type,
                                nodata,
                                cell_size)
