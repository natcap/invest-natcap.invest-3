import logging

import os

from osgeo import gdal, ogr, osr
gdal.UseExceptions()

from invest_natcap import raster_utils

import json

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('agriculture')

def datasource_from_dataset_bounding_box_uri(dataset_uri, datasource_uri):
    """Creates a shapefile with the bounding box from a raster.

    :param dataset_uri: The uri for the input raster.
    :type dataset_uri: str

    :return: None
    :rtype: None
    """
    LOGGER.debug("Creating extent from: %s", dataset_uri)
    LOGGER.debug("Storing extent in: %s", datasource_uri)
    geotransform = raster_utils.get_geotransform_uri(dataset_uri)
    bounding_box = raster_utils.get_bounding_box(dataset_uri)
    upper_left_x, upper_left_y, lower_right_x, lower_right_y = bounding_box

    driver = ogr.GetDriverByName('ESRI Shapefile')

    if os.path.exists(datasource_uri):
        driver.DeleteDataSource(datasource_uri)

    datasource = driver.CreateDataSource(datasource_uri)
    if datasource is None:
        msg = "Could not create %s." % datasource_uri
        LOGGER.error(msg)
        raise IOError, msg

    dataset = gdal.Open(dataset_uri)

    field_name = "Id"
    field_value = 1

    #add projection
    srs = osr.SpatialReference()
    srs.ImportFromWkt(dataset.GetProjectionRef())

    #create layer with field definitions
    layer = datasource.CreateLayer("raster", geom_type = ogr.wkbPolygon, srs = srs)
    field_defn = ogr.FieldDefn(field_name,ogr.OFTInteger)
    layer.CreateField(field_defn)

    feature_defn = layer.GetLayerDefn()

    #create polygon
    polygon = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)

    ring.AddPoint(upper_left_x, upper_left_y)
    ring.AddPoint(lower_right_x, upper_left_y)
    ring.AddPoint(lower_right_x, lower_right_y)
    ring.AddPoint(upper_left_x, lower_right_y)
    ring.AddPoint(upper_left_x, upper_left_y)

    ring.CloseRings()
    polygon.AddGeometry(ring)

    # create a new feature
    feature = ogr.Feature(feature_defn)
    feature.SetGeometry(polygon)
    feature.SetField(field_name, field_value)

    layer.CreateFeature(feature)

    #clean up and write to disk
    polygon = None
    feature = None

    datasource = None

def sum_uri(dataset_uri):
    """Wrapper call to raster_utils.aggregate_raster_values_uri to extract total

    :param dataset_uri: The uri for the input raster.
    :type dataset_uri: str

    :return: None
    :rtype: None
    """
    datasource_uri = raster_utils.temporary_filename() + ".shp"
    datasource_from_dataset_bounding_box_uri(dataset_uri, datasource_uri)

    total = raster_utils.aggregate_raster_values_uri(dataset_uri, datasource_uri).total
    return total.__getitem__(total.keys().pop())

def calculate_nutrition(crop_uri,
                        yield_type,
                        nutrient_table,
                        nutrient_selection,
                        output_dir,
                        file_name_pattern,
                        invest_crops = {},
                        nutrient_aliases={},
                        gdal_type = gdal.GDT_Float32,
                        nodata_crop = 0,
                        nodata_nutrient = -1):
    output_uri_list = []
    for nutrient in nutrient_selection:
        if nutrient in nutrient_aliases:
            LOGGER.debug("Creating %s raster.", nutrient_aliases[nutrient])
        else:
            LOGGER.debug("Creating %s raster.", nutrient)

        reclass_table = {}
        if invest_crops == {}:
            raise ValueError, "I need to make a call to unique values here."
        
        for crop in invest_crops:
            try:
                reclass_table[crop] = nutrient_table[crop][nutrient]
            except KeyError:
                LOGGER.warn("No nutrition information for crop %i, setting values to %s.",
                            crop,
                            nodata_nutrient)
                reclass_table[crop] = nodata_nutrient

        reclass_table[nodata_crop] = nodata_nutrient

        if nutrient in nutrient_aliases:
            nutrient_uri = os.path.join(output_dir,
                                        file_name_pattern % (yield_type,
                                                             nutrient_aliases[nutrient]))
        else:
            nutrient_uri = os.path.join(output_dir,
                                        file_name_pattern % (yield_type,
                                                             nutrient))

        LOGGER.debug("Creating raster: %s", nutrient_uri)

        raster_utils.reclassify_dataset_uri(crop_uri,
                                        reclass_table,
                                        nutrient_uri,
                                        gdal_type,
                                        nodata_nutrient,
                                        exception_flag = "values_required",
                                        assert_dataset_projected = False)

        output_uri_list.append(nutrient_uri)

    return output_uri_list

def crop_production_existing_projected(reclass_crop_cover_uri,
                                       yield_uri,
                                       yield_op,
                                       area_uri,
                                       area_op,
                                       extent_4326_uri,
                                       clip_yield_uri,
                                       project_yield_uri,
                                       crop_yield_uri,
                                       clip_area_uri,
                                       project_area_uri,
                                       crop_area_uri,
                                       crop_production_uri,
                                       cell_size,
                                       output_wkt,
                                       gdal_type_float,
                                       nodata_float):

    def production_op(crop_yield, crop_area):
        if nodata_float in [crop_yield, crop_area]:
            return nodata_float
        else:
            return crop_yield * crop_area


    ##process yield dataset
    #clip
    raster_utils.clip_dataset_uri(yield_uri,
                                  extent_4326_uri,
                                  clip_yield_uri,
                                  assert_projections=False)
    #project
    raster_utils.warp_reproject_dataset_uri(clip_yield_uri,
                                            cell_size,
                                            output_wkt,
                                            "nearest",
                                            project_yield_uri)
    #mask
    raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                     project_yield_uri],
                                    yield_op,
                                    crop_yield_uri,
                                    gdal_type_float,
                                    nodata_float,
                                    cell_size,
                                    "dataset",
                                    dataset_to_bound_index=0)

    ##process area dataset
    #clip
    raster_utils.clip_dataset_uri(area_uri,
                                  extent_4326_uri,
                                  clip_area_uri,
                                  assert_projections=False)
    #project
    raster_utils.warp_reproject_dataset_uri(clip_area_uri,
                                            cell_size,
                                            output_wkt,
                                            "nearest",
                                            project_area_uri)
    #mask
    raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                     project_area_uri],
                                    area_op,
                                    crop_area_uri,
                                    gdal_type_float,
                                    nodata_float,
                                    cell_size,
                                    "dataset",
                                    dataset_to_bound_index=0)

    ##calculate production
    raster_utils.vectorize_datasets([crop_yield_uri,
                                     crop_area_uri],
                                    production_op,
                                    crop_production_uri,
                                    gdal_type_float,
                                    nodata_float,
                                    cell_size,
                                    "dataset",
                                    dataset_to_bound_index=0)

def calculate_production_existing(reclass_crop_cover_uri,
                                  raster_table,
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
                                  projected=True):

    nodata_yield = -9999
    def yield_op_closure(crop):
        def yield_op(cover, crop_yield):
            if crop_yield == nodata_yield or cover != crop:
                return nodata_float
            else:
                return crop_yield

        return yield_op

    nodata_area = -9999
    def area_op_closure(crop):
        def area_op(cover, crop_area):
            if crop_area == nodata_area or cover != crop:
                return nodata_float
            else:
                return crop_area

        return area_op


    output_list = []
    if projected:
        for crop in invest_crops:
            LOGGER.debug("Separating out crop %i.", crop)
            yield_uri = os.path.join(raster_path, raster_table[crop][raster_table_field_yield])
            area_uri = os.path.join(raster_path, raster_table[crop][raster_table_field_area])

            clip_yield_uri = os.path.join(intermediate_uri, clip_yield_name % crop)
            project_yield_uri = os.path.join(intermediate_uri, projected_yield_name % crop)
            crop_yield_uri = os.path.join(intermediate_uri, crop_yield_name % crop)

            clip_area_uri = os.path.join(intermediate_uri, clip_area_name % crop)
            project_area_uri = os.path.join(intermediate_uri, projected_area_name % crop)
            crop_area_uri = os.path.join(intermediate_uri, crop_area_name % crop)

            crop_production_uri = os.path.join(intermediate_uri, crop_production_name % crop)

            crop_production_existing_projected(reclass_crop_cover_uri,
                                               yield_uri,
                                               yield_op_closure(crop),
                                               area_uri,
                                               area_op_closure(crop),
                                               extent_4326_uri,
                                               clip_yield_uri,
                                               project_yield_uri,
                                               crop_yield_uri,
                                               clip_area_uri,
                                               project_area_uri,
                                               crop_area_uri,
                                               crop_production_uri,
                                               cell_size,
                                               output_wkt,
                                               gdal_type_float,
                                               nodata_float)
            

            output_list.extend([yield_uri, area_uri,
                                clip_yield_uri,
                                project_yield_uri,
                                crop_yield_uri,
                                clip_area_uri,
                                project_area_uri,
                                crop_area_uri,
                                crop_production_uri])


    else:
        raise ValueError, "Not implementd."


def calculate_valuation():
    pass

def execute(args):
    config_uri = os.path.join(os.path.dirname(__file__), "config.json")
    LOGGER.debug("Loading configuration file: %s", config_uri)
    config = json.loads(open(config_uri).read())
  
    gdal_type_cover = gdal.GDT_Int32
    gdal_type_float = gdal.GDT_Float32
    nodata_int = 0
    nodata_float = 0.0

    table_precision = 2

    intermediate_dir = "intermediate"

    reclass_name = "crop_reclass.tif"

    report_name = "report.htm"

    use_existing_crops = args["enable_tab_existing"]
    use_percentile_crops = args["enable_tab_percentile"]
    use_modeled_crops = args["enable_tab_modeled"]

    if not any([use_existing_crops,
                use_percentile_crops,
                use_modeled_crops]):
        LOGGER.error("You must select at least one crop yield method.")
        raise ValueError, "You must select at least one crop yield method."
        

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

    crop_yield_name = "%i_yield_masked.tif"
    clip_yield_name = "%i_yield_clip.tif"
    projected_yield_name = "%i_yield_prj.tif"

    crop_area_name = "%i_area_masked.tif"
    clip_area_name = "%i_area_clip.tif"
    projected_area_name = "%i_area_prj.tif"

    crop_production_name = "%i_prod.tif"

##    statistics = {}
##    statistics_field_production = "Production"
##    statistics_field_intensity = "Intensity (%)"

    intermediate_uri = os.path.join(workspace_dir, intermediate_dir)

    if not os.path.exists(os.path.join(workspace_dir, intermediate_dir)):
        os.makedirs(os.path.join(workspace_dir, intermediate_dir))

    reclass_crop_cover_uri = os.path.join(intermediate_uri,
                                          reclass_name)

    report_uri = os.path.join(workspace_dir, report_name)

    nutrient_name = "%s_nutrient_%s.tif"

    valuation_table_field_subregion = "Subregion"

    subregion_uri = args["valuation_raster"]
    subregion_clip_name = "subregion_clip.tif"
    subregion_project_name = "subregion_project.tif"

    valuation_csv_uri = args["valuation_table"]
    valuation_field_id = "Id"
    valuation_csv_dict = raster_utils.get_lookup_from_csv(valuation_csv_uri,
                                                          valuation_field_id)
    valuation_field_N_cost = "avg_N"
    valuation_field_P_cost = "avg_P"
    valuation_field_K_cost = "avg_K"
    valuation_field_labor_cost = "laborcost"
    valuation_field_machine_cost = "actual_mach"
    valuation_field_seed_cost = "actual_seed"
    valuation_field_crop_cost = "avgPP"

    field_returns = "Return"
    field_irrigation = "Irrigation"
    field_fertilizer = "Fertilizer"

    fertilizer_name = "%i_%s.tif"
    fertilizer_prj_name = "%i_%s_prj.tif"
    fertilizer_cost_name = "%i_%s_cost.tif"

    extent_name = "extent.shp"
    extent_4326_name = "extent_4326.shp"
    sr_4326 = osr.SpatialReference()
    sr_4326.ImportFromEPSG(4326)
    wkt = sr_4326.ExportToWkt()
    extent_uri = os.path.join(intermediate_uri, extent_name)
    extent_4326_uri = os.path.join(intermediate_uri, extent_4326_name)

    output_wkt = raster_utils.get_dataset_projection_wkt_uri(crop_cover_uri)

    datasource_from_dataset_bounding_box_uri(crop_cover_uri, extent_uri)

    raster_utils.reproject_datasource_uri(extent_uri, wkt, extent_4326_uri)
       
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

    projected=True
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

##    statistics[crop] = {}
##    statistics[crop][statistics_field_production] = sum_uri(crop_production_uri) * cell_size
##    statistics[crop][statistics_field_intensity] = 100 * sum_uri(crop_area_uri) / invest_crop_counts[crop]

    if args["calculate_nutrition"]:
        #load nutrition table
        nutrition_table_dict = raster_utils.get_lookup_from_csv(args["nutrition_table"],
                                                                config["nutrition_table"]["id_field"])
        #construct dictionary for included nutrients
        nutrient_selection = {}
        nutrient_aliases = {}
        for nutrient in config["nutrition_table"]["columns"]:
            if args[config["nutrition_table"]["columns"][nutrient]["args_id"]]:
                LOGGER.debug("Including nutrient %s in analysis.", nutrient)
                nutrient_selection[nutrient] = True
                nutrient_aliases[nutrient] = config["nutrition_table"]["columns"][nutrient]["formatting"]["abbreviation"]

        yield_type = "existing"                
        calculate_nutrition(reclass_crop_cover_uri,
                            yield_type,
                            nutrition_table_dict,
                            nutrient_selection,
                            intermediate_uri,
                            nutrient_name,
                            invest_crops,
                            nutrient_aliases)


    if args["calculate_valuation"]:
        LOGGER.debug("Calculating valuation.")
        LOGGER.debug("Determining geographic subregion(s).")
        subregion_clip_uri = os.path.join(intermediate_uri, subregion_clip_name)
        subregion_project_uri = os.path.join(intermediate_uri, subregion_project_name)

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
        #count regions
        subregion_counts = raster_utils.unique_raster_values_count(subregion_project_uri)
        subregions = subregion_counts.keys()
        subregions.sort()

        if len(subregions) == 0:
            LOGGER.info("There is no valuation data for your area.")
        elif len(subregions) == 1:
            def fertilizer_cost_closure(crop, cost):
                def fertilizer_op(cover, fertilizer):
                    if (cover == nodata_int) or (cover != crop):
                        return nodata_float
                    else:
                        return cost * fertilizer

                return fertilizer_op

            region = subregions[0]

            LOGGER.info("Your data falls entirely within region %i.", region)
            LOGGER.debug("Calculating fertilizer.")
            LOGGER.debug("Clipping fertilizer raster.")
            for crop in invest_crops:

                fertilizer_uri = raster_table_csv_dict[crop][raster_table_field_K2O]
                if fertilizer_uri != "":
                    fertilizer_uri = os.path.join(raster_path, fertilizer_uri)
                    LOGGER.debug("Cropping fertilizer K2O for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])
                    cropped_uri = os.path.join(intermediate_uri,
                                               fertilizer_name % (crop,
                                                                  raster_table_field_K2O))

                    raster_utils.clip_dataset_uri(fertilizer_uri,
                                                  extent_4326_uri,
                                                  cropped_uri,
                                                  assert_projections=False)

                    LOGGER.debug("Projecting clipped fertilizer K20 for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])
                    projected_uri = os.path.join(intermediate_uri,
                                                 fertilizer_prj_name % (crop,
                                                                        raster_table_field_K2O))
                    raster_utils.warp_reproject_dataset_uri(cropped_uri,
                                                            cell_size,
                                                            output_wkt,
                                                            "nearest",
                                                            projected_uri)
                    try:
                        cost = valuation_csv_dict[str((region, crop))][valuation_field_K_cost]
                        LOGGER.debug("Calculating cost raster for fertilizer %s for %s.",
                                     raster_table_field_K2O,
                                     raster_table_csv_dict[crop][raster_table_field_short_name])
                        fertilizer_cost_uri = os.path.join(intermediate_uri, fertilizer_cost_name % (crop,
                                                                                                     raster_table_field_K2O))
                        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                                          projected_uri],
                                                         fertilizer_cost_closure(crop, cost),
                                                         fertilizer_cost_uri,
                                                         gdal_type_float,
                                                         nodata_float,
                                                         cell_size,
                                                         "dataset",
                                                         dataset_to_bound_index=0)
                    except KeyError:
                        LOGGER.warning("Cost data for fertilizer %s NOT available in region %i.")

                else:
                    LOGGER.warning("Fertilizer K2O unavaiable for %s.",
                                   raster_table_csv_dict[crop][raster_table_field_short_name])

                fertilizer_uri = raster_table_csv_dict[crop][raster_table_field_N]
                if fertilizer_uri != "":
                    fertilizer_uri = os.path.join(raster_path, fertilizer_uri)
                    LOGGER.debug("Cropping fertilizer N for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])

                    cropped_uri = os.path.join(intermediate_uri,
                                               fertilizer_name % (crop,
                                                                  raster_table_field_N))

                    raster_utils.clip_dataset_uri(fertilizer_uri,
                                                  extent_4326_uri,
                                                  cropped_uri,
                                                  assert_projections=False)

                    LOGGER.debug("Projecting clipped fertilizer N for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])
                    projected_uri = os.path.join(intermediate_uri,
                                                 fertilizer_prj_name % (crop,
                                                                        raster_table_field_N))
                    raster_utils.warp_reproject_dataset_uri(cropped_uri,
                                                            cell_size,
                                                            output_wkt,
                                                            "nearest",
                                                            projected_uri)
                    try:
                        cost = valuation_csv_dict[str((region, crop))][valuation_field_N_cost]
                        LOGGER.debug("Calculating cost raster for fertilizer %s for %s.",
                                     raster_table_field_N,
                                     raster_table_csv_dict[crop][raster_table_field_short_name])
                        fertilizer_cost_uri = os.path.join(intermediate_uri, fertilizer_cost_name % (crop,
                                                                                                     raster_table_field_N))
                        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                                          projected_uri],
                                                         fertilizer_cost_closure(crop, cost),
                                                         fertilizer_cost_uri,
                                                         gdal_type_float,
                                                         nodata_float,
                                                         cell_size,
                                                         "dataset",
                                                         dataset_to_bound_index=0)
                        
                    except KeyError:
                        LOGGER.warning("Cost data for fertilizer %s NOT available in region %i.")

                else:
                    os.path.join(raster_path, fertilizer_uri)
                    LOGGER.debug("Fertilizer N unavailable for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])

                fertilizer_uri = raster_table_csv_dict[crop][raster_table_field_P2O5]
                if fertilizer_uri != "":
                    fertilizer_uri = os.path.join(raster_path, fertilizer_uri)
                    LOGGER.debug("Cropping fertilizer P2O5 for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])

                    cropped_uri = os.path.join(intermediate_uri,
                                               fertilizer_name % (crop,
                                                                  raster_table_field_P2O5))

                    raster_utils.clip_dataset_uri(fertilizer_uri,
                                                  extent_4326_uri,
                                                  cropped_uri,
                                                  assert_projections=False)

                    LOGGER.debug("Projecting clipped fertilizer P2O5 for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])
                    projected_uri = os.path.join(intermediate_uri,
                                                 fertilizer_prj_name % (crop,
                                                                        raster_table_field_P2O5))
                    raster_utils.warp_reproject_dataset_uri(cropped_uri,
                                                            cell_size,
                                                            output_wkt,
                                                            "nearest",
                                                            projected_uri)
                    try:
                        cost = valuation_csv_dict[str((region, crop))][valuation_field_P_cost]
                        LOGGER.debug("Calculating cost raster for fertilizer %s for %s.",
                                     raster_table_field_P2O5,
                                     raster_table_csv_dict[crop][raster_table_field_short_name])
                        fertilizer_cost_uri = os.path.join(intermediate_uri, fertilizer_cost_name % (crop,
                                                                                                     raster_table_field_P2O5))
                        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                                          projected_uri],
                                                         fertilizer_cost_closure(crop, cost),
                                                         fertilizer_cost_uri,
                                                         gdal_type_float,
                                                         nodata_float,
                                                         cell_size,
                                                         "dataset",
                                                         dataset_to_bound_index=0)

                    except KeyError:
                        LOGGER.warning("Cost data for fertilizer %s NOT available in region %i.")

                else:
                    LOGGER.debug("Fertilizer P2O5 unavailable for %s.",
                                 raster_table_csv_dict[crop][raster_table_field_short_name])

            LOGGER.debug("Calculating fertilizer cost.")


            LOGGER.debug("Calculating irrigation cost.")
            LOGGER.debug("Calculating labor cost.")
            LOGGER.debug("Calculatiing machine cost.")
            LOGGER.debug("Calculating seed cost.")

            valuation_field_N_cost = "avg_N"
            valuation_field_P_cost = "avg_P"
            valuation_field_K_cost = "avg_K"
            valuation_field_labor_cost = "laborcost"
            valuation_field_machine_cost = "actual_mach"
            valuation_field_seed_cost = "actual_seed"
            valuation_field_crop_cost = "avgPP"

            for crop in invest_crops:
                region_crop = str((region, crop))

                if region_crop in valuation_csv_dict:
                    LOGGER.debug("Agricultural cost data available for crop %i in region %i.", crop, region)
                    price = valuation_csv_dict[region_crop][valuation_field_crop_cost]
##                    intensity = statistics[crop][statistics_field_intensity]
                    area = invest_crop_counts[crop] * cell_size
                    labor = valuation_csv_dict[region_crop][valuation_field_labor_cost]
                    machine = valuation_csv_dict[region_crop][valuation_field_machine_cost]
                    seed = valuation_csv_dict[region_crop][valuation_field_seed_cost]

##                    statistics[crop][valuation_field_crop_cost] = price * intensity * area
##                    statistics[crop][valuation_field_labor_cost] = -1 * labor * intensity * area
##                    statistics[crop][valuation_field_machine_cost] = -1 * machine * intensity * area
##                    statistics[crop][valuation_field_seed_cost] = -1 * seed * intensity * area
##                    statistics[crop][field_returns] = sum([statistics[crop][valuation_field_crop_cost],
##                                                           statistics[crop][valuation_field_labor_cost],
##                                                           statistics[crop][valuation_field_machine_cost],
##                                                           statistics[crop][valuation_field_seed_cost]])
##
##                    statistics[crop][field_irrigation] = ""
##                    statistics[crop][field_fertilizer] = ""

                else:
                    LOGGER.warn("Agricultural cost data NOT available for crop %i in region %i.", crop, region)
##                    statistics[crop][valuation_field_crop_cost] = ""
##                    statistics[crop][valuation_field_labor_cost] = ""
##                    statistics[crop][valuation_field_machine_cost] = ""
##                    statistics[crop][valuation_field_seed_cost] = ""
##                    statistics[crop][field_returns] = ""
##                    statistics[crop][field_irrigation] = ""
##                    statistics[crop][field_fertilizer] = ""


        else:
            LOGGER.info("Your data falls within the following regions: %s", ", ".join(subregions))
            raise ValueError, "Not supported."
            for region in subregions:
                LOGGER.debug("Calculating statistics for region %i.", region)

        #create region masks

##    #create report
##    for crop in statistics:
##        for stat in statistics[crop].keys():
##            try:
##                statistics[crop][stat] = round(statistics[crop][stat], table_precision)
##            except TypeError:
##                statistics[crop][stat] = "NA"
##
##    report = open(report_uri, 'w')
##    report.write("<HTML>")
##
##    #cover summary
##    LOGGER.debug("Generating coverage table.")
##    report.write("<B>Crop Cover</B>")
##    report.write("\n<TABLE BORDER=1>")
##    row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3)
##    row_html += ("<TD ALIGN=RIGHT>%s</TD>" * 3) + "</TR>"
##    report.write(row_html % (reclass_table_field_key,
##                             reclass_table_field_invest,
##                             raster_table_field_short_name,
##                             "Extent (m^2)",
##                             statistics_field_intensity,
##                             statistics_field_production))
##
##    crop_counts = raster_utils.unique_raster_values_count(crop_cover_uri)
##    crop_counts_keys = crop_counts.keys()
##    crop_counts_keys.sort()
##
##    if crop_counts_keys[0] == 0:
##        crop_counts_keys.pop(0)
##
##    for crop in crop_counts_keys:
##        LOGGER.debug("Writing crop %i yield statistics to table.", crop)
##        invest_crop = reclass_table_csv_dict[crop][reclass_table_field_invest]
##        report.write(row_html % (str(crop),
##                                 str(invest_crop),
##                                 raster_table_csv_dict[invest_crop][raster_table_field_short_name],
##                                 str(round(crop_counts[crop] * cell_size, table_precision)),
##                                 statistics[invest_crop][statistics_field_intensity],
##                                 str(round(statistics[invest_crop][statistics_field_production], table_precision))))
##
##    report.write("\n</TABLE>")
##
##    #nutrition summary
##    if args["calculate_nutrition"]:
##        LOGGER.info("Generating nutrition table.")
##
##        report.write("\n<P><B>Nutrition</B>")
##
##        report.write("\n<TABLE BORDER=1>")
##        row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3)
##        row_html += ("<TD ALIGN=RIGHT>%s</TD>" * len(nutrient_selection)) + "</TR>"
##        header_row = [reclass_table_field_key,
##                      reclass_table_field_invest,
##                      raster_table_field_short_name]
##        for nutrient in nutrient_selection:
##            header_row.append(nutrition_table_fields[nutrient])
##        report.write(row_html % tuple(header_row))
##
##        for crop in crop_counts_keys:
##            LOGGER.debug("Writing crop %i nutrtion statistics to table.", crop)
##            invest_crop = reclass_table_csv_dict[crop][reclass_table_field_invest]
##
##            row = [str(crop),
##                   str(invest_crop),
##                   raster_table_csv_dict[invest_crop][raster_table_field_short_name]]
##
##            row += [statistics[invest_crop][nutrient] for nutrient in nutrient_selection]
##
##            report.write(row_html % tuple(row))
##
##        report.write("\n</TABLE>")
##
##    if args["calculate_valuation"]:
##        LOGGER.debug("Generating fertilizer table.")
##        report.write("\n<P><B>Fertilizer</B>")
##
##        LOGGER.debug("Generating valuation table.")
##        report.write("\n<P><B>Valuation</B>")
##        report.write("\n<TABLE BORDER=1>")
##        row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3) + ("<TD ALIGN=RIGHT>%s</TD>" * 7) + "</TR>"
##
##        header_row = (reclass_table_field_key,
##                      reclass_table_field_invest,
##                      raster_table_field_short_name,
##                      "Production",
##                      "Irrigation",
##                      "Fertilizer",
##                      "Labor",
##                      "Machines",
##                      "Seeds",
##                      "Returns")
##
##        report.write(row_html % header_row)
##
##        for crop in crop_counts_keys:
##            LOGGER.debug("Writing crop %i valutation statistics to table.", crop)
##            invest_crop = reclass_table_csv_dict[crop][reclass_table_field_invest]
##            report.write(row_html % (str(crop),
##                                     str(invest_crop),
##                                     raster_table_csv_dict[invest_crop][raster_table_field_short_name],
##                                     statistics[crop][valuation_field_crop_cost],
##                                     statistics[crop][field_irrigation],
##                                     statistics[crop][field_fertilizer],
##                                     statistics[crop][valuation_field_labor_cost],
##                                     statistics[crop][valuation_field_machine_cost],
##                                     statistics[crop][valuation_field_seed_cost],
##                                     statistics[crop][field_returns]))
##
##
##        report.write("\n</TABLE>")
##
##    report.write("\n</HTML>")
##    report.close()
