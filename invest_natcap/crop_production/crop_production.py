import logging

import os

from osgeo import gdal, ogr, osr
gdal.UseExceptions()

from invest_natcap import raster_utils

import json

import operator

import numpy

import sys

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('crop_production')

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


def calculate_valuation(crop_uri,
                        intensity_uri,
                        subregion_uri,
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
                        gdal_type=gdal.GDT_Float32,
                        nodata = -1,
                        cell_size = None):

    if cell_size == None:
        cell_size = raster_utils.get_cell_from_uri(crop_uri)
    
    def valuation_closure_op(field_key):
        def valuation_op(crop, subregion, quantity):
            if nodata in [crop, subregion, quantity]:
                return nodata
            else:
                try:
                    return valuation_dict[(subregion, crop)][field_key] * quantity
                except KeyError:
                    return nodata

    def mul_op(*values):
        if nodata in values:
            return nodata
        else:
            return reduce(operator.mul, values)


    valuation_list = [("nitrogen", nitrogen_uri, field_nitrogen, nitrogen_cost_uri),
                      ("phosphorus", phosphorus_uri, field_phosphorus, phosphorus_cost_uri),
                      ("potassium", potassium_uri, field_potassium, potassium_cost_uri),
                      ("irrigation", irrigation_uri, field_irrigation, irrigation_cost_uri),
                      ("labor", labor_uri, field_labor, labor_cost_uri),
                      ("machine", machine_uri, field_machine, machine_cost_uri),
                      ("seed", seed_uri, field_seed, seed_cost_uri)]

    for component_label, componet_uri, component_field, cost_uri in valuation_list:

        
        if component_field != None:
            LOGGER.debug("Calculating %s cost using valuation table field %s.",
                         component_label,
                         component_field)        
            raster_utils.vectorize_datasets([crop_uri, subregion_uri, component_uri],
                                        valuation_closure_op(component_field),
                                        cost_uri,
                                        gdal_type,
                                        nodata,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0)
        else:
            LOGGER.debug("Calculating %s cost using cost raster.", component_label)
            raster_utils.vectorize_datasets([intensity_uri, component_uri],
                                            mul_op,
                                            cost_uri,
                                            gdal_type,
                                            nodata,
                                            cell_size,
                                            "dataset",
                                            dataset_to_bound_index=0)


def preprocess_fertilizer(crop_uri,
                          crop_list,
                          cell_size,
                          output_wkt,
                          raster_table,
                          raster_field,
                          raster_path,
                          extent_uri,
                          dataset_uri,
                          gdal_type = gdal.GDT_Float32,
                          unknown_crop = 0,
                          place_holder = -2,
                          nodata = -1.0):

    def extract_closure(labeled_raster_uri, uri_dict):
        nodata = raster_utils.get_nodata_from_uri(labeled_raster_uri)
        labels = list(raster_utils.unique_raster_values_count(labeled_raster_uri).keys())
        labels.sort()

        raster_list = [labeled_raster_uri] + [uri_dict[l] for l in labels]
        raster_index = dict(zip(labels, range(len(labels))))
        
        def extract_op(*values):
            array = numpy.ones(values[0].shape) * nodata
            for v in labels:
                array = numpy.where(values[0] == v, values[raster_index[int(v)]+1], array)
            array = numpy.where(array == place_holder, nodata, array)                    

            return array

        return raster_list, extract_op

    nodata_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(crop_uri,
                                          nodata_uri,
                                          "GTiff",
                                          nodata,
                                          gdal.GDT_Int32,
                                          fill_value=place_holder)

    fertilizer_dict = {unknown_crop : nodata_uri}
    for crop in crop_list:
        if raster_table[crop][raster_field] == "":
            fertilizer_dict[crop] = nodata_uri
        else:
            try:
                LOGGER.debug("Clipping global %s raster for InVEST crop %i.", raster_field, crop)
                dataset_in_uri = os.path.join(raster_path, raster_table[crop][raster_field])
                
                clip_uri = raster_utils.temporary_filename()

                raster_utils.clip_dataset_uri(dataset_in_uri,
                                              extent_uri,
                                              clip_uri,
                                              assert_projections=False)
                
                LOGGER.debug ("Projecting clipped %s raster for InVEST crop %i.", raster_field, crop)
                clip_prj_uri = raster_utils.temporary_filename()


                raster_utils.warp_reproject_dataset_uri(clip_uri,
                                                        cell_size,
                                                        output_wkt,
                                                        "nearest",
                                                        clip_prj_uri)

                fertilizer_dict[crop] = clip_prj_uri

            except:
                e = sys.exc_info()[1]

                if str(e) == "The datasets' intersection is empty (i.e., not all the datasets touch each other).":
                    LOGGER.warning("Nitrogen fertilizer data is not available for InVEST crop %i.", crop)                
                    fertilizer_dict[crop] = nodata_uri
                    
                else:
                    raise e
        
    LOGGER.info("Creating nitrogen raster.")
    raster_list, extract_op = extract_closure(crop_uri, fertilizer_dict)

    raster_utils.vectorize_datasets(raster_list,
                                    extract_op,
                                    dataset_uri,
                                    gdal_type,
                                    nodata,
                                    cell_size,
                                    "dataset",
                                    dataset_to_bound_index=0,
                                    dataset_to_align_index=0,
                                    vectorize_op=False)

class ReclassLookup:
    def __init__ (self, d, field, nodata=-1):
        self.d = d
        self.nodata = nodata

    def __getitem__(self, k):
        try:
            return float(self.d[k][field])
        except KeyError, ValueError:
            return nodata

    def __repr__(self):
        return repr(self.d)

def lookup_reclass_closure(lookup, field, nodata=-1):
    def lookup_reclass_op(crop, region):
        try:
            return float(lookup["(%i, %i)" % (region, crop)][field])
        except KeyError, ValueError:
            return nodata

    return lookup_reclass_op


def mul_closure(nodata_list, nodata):
    def mul_op(*values):
        if any([apply(operator.eq, pair) for pair in zip(values, nodata_list)]):
            return nodata
        else:
            return reduce(operator.mul, values)

    return mul_op

class NoKeyErrorDict:
    def __init__(self, d, key_error_value):
        self.d = d
        self.key_error_value = key_error_value

    def __getitem__(self, k):
        try:
            return self.d[k]
        except KeyError:
            return key_error_value

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

    raster_table_field_climate = "Climate"

    crop_yield_name = "%i_yield_masked.tif"
    clip_yield_name = "%i_yield_clip.tif"
    projected_yield_name = "%i_yield_prj.tif"

    crop_area_name = "%i_area_masked.tif"
    clip_area_name = "%i_area_clip.tif"
    projected_area_name = "%i_area_prj.tif"

    crop_production_name = "%i_prod.tif"

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

    datasource_from_dataset_bounding_box_uri(crop_cover_uri, extent_uri)

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

            preprocess_fertilizer(reclass_crop_cover_uri,
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
                                        lookup_reclass_closure(valuation_csv_dict,
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
                                        mul_closure([nodata_float, nodata_float], nodata_float),
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

            preprocess_fertilizer(reclass_crop_cover_uri,
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
                                        lookup_reclass_closure(valuation_csv_dict,
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
                                        mul_closure([nodata_float, nodata_float], nodata_float),
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

            preprocess_fertilizer(reclass_crop_cover_uri,
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
                                        lookup_reclass_closure(valuation_csv_dict,
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
                                        mul_closure([nodata_float, nodata_float], nodata_float),
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
                                            lookup_reclass_closure(valuation_csv_dict,
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
                                            lookup_reclass_closure(valuation_csv_dict,
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
                                            lookup_reclass_closure(valuation_csv_dict,
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
                                        lookup_reclass_closure(valuation_csv_dict,
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


    if args["enable_tab_existing"]:

        yield_uri = os.path.join(intermediate_uri, "yield_existing.tif")
        
        preprocess_fertilizer(reclass_crop_cover_uri,
                          invest_crops,
                          cell_size,
                          output_wkt,
                          raster_table_csv_dict,
                          raster_table_field_yield,
                          raster_path,
                          extent_4326_uri,
                          yield_uri)

        area_uri = os.path.join(intermediate_uri, "harea_existing.tif")
        preprocess_fertilizer(reclass_crop_cover_uri,
                          invest_crops,
                          cell_size,
                          output_wkt,
                          raster_table_csv_dict,
                          raster_table_field_area,
                          raster_path,
                          extent_4326_uri,
                          area_uri)

    if args["enable_tab_existing"]:
        climate_uri = os.path.join(intermediate_uri, "climate.tif")

        preprocess_fertilizer(reclass_crop_cover_uri,
                          invest_crops,
                          cell_size,
                          output_wkt,
                          raster_table_csv_dict,
                          raster_table_field_climate,
                          raster_path,
                          extent_4326_uri,
                          climate_uri)
        
        yield_uri = os.path.join(intermediate_uri, "yield_percentile.tif")

        
                                

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
