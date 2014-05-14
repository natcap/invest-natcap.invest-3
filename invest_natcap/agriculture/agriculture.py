import logging

import os

from osgeo import gdal, ogr, osr
gdal.UseExceptions()

from invest_natcap import raster_utils

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

def execute(args):
    gdal_type_cover = gdal.GDT_Int32
    gdal_type_float = gdal.GDT_Float32
    nodata_int = -1
    nodata_float = -1.0
    
    intermediate_dir = "intermediate"

    reclass_name = "crop_reclass.tif"
    
    report_name = "report.htm"

    workspace_dir = args["workspace_dir"]
    crop_cover_uri = args["crop_file_name"]

    reclass_table_uri = args["reclass_table"]
    reclass_table_field_key = "Input Value"
    reclass_table_field_invest = "InVEST Value"

    raster_table_uri = args["raster_table"]
    raster_path = os.path.dirname(raster_table_uri)
    raster_table_field_key = "Id"
    raster_table_field_short_name = "Short Name"
    raster_table_other_short_name = "Other"

    raster_table_field_yield = "Monfreda_yield"

    crop_yield_name = "%i_yield.tif"
    
    statistics = {}
    statistics_field_production = "Production"

    intermediate_uri = os.path.join(workspace_dir, intermediate_dir)
    
    reclass_crop_cover_uri = os.path.join(intermediate_uri,
                                          reclass_name)
    
    report_uri = os.path.join(workspace_dir, report_name)

    if args["calculate_nutrition"]:
        nutrition_table_uri = args["nutrition_table"]
        
        nutrition_table_fields = {"Protein (N x 6.25) g per 100 g" : "protein",
                                  "Total lipid (g per 100 g)" : "lipids",
                                  "Energy (kj) per 100 g" : "kJ",
                                  "Calcium (g per 100g)" : "Ca",
                                  "Iron (g per 100g)" : "Fe",
                                  "Magnesium (g per 100g)" : "Mg",
                                  "Phosphorus (g per 100g)" : "P",
                                  "Potassium (g per 100 g)" : "K",
                                  "Sodium (g per 100g)" : "Na",
                                  "Zinc (g per 100g)" : "Zn",
                                  "Copper (g per 100g)" : "Cu",
                                  "Fluoride  F (g per 100g)" : "F",
                                  "Manganese (g per 100g)" : "Mn",
                                  "Selenium (g per 100g)" : "Se",
                                  "Vitamin A (IU per 100g)" : "vit_A",
                                  "Carotene  beta (g per 100g)": "carotene_B",
                                  "Carotene  alpha (g per 100g)" : "carotene_A",
                                  "Vitamin E (alpha-tocopherol) g per 100g" : "vit_E",
                                  "Cryptoxanthin  beta (g per 100g)" : "C_xanthin_B",
                                  "Lycopene (g per 100g)" : "lycopene",
                                  "Lutein + zeaxanthin (g per 100g)" : "Lutein_Zeaxanthin",
                                  "Tocopherol  beta (g per 100g)" : "Tocopherol_B",
                                  "Tocopherol gamma (g per 100g)" : "Tocopherol_G",
                                  "Tocopherol  Delta (g per 100g)" : "Tocopherol_D",
                                  "Vitamin C (g per 100g)" : "vit_C",
                                  "Thiamin (g per 100g)" : "vit_B1",
                                  "Riboflavin (g per 100g)" : "vit_B2",
                                  "Niacin (g per 100g)" : "vit_B3",
                                  "Pantothenic acid (g per 100 g)" : "vit_B5",
                                  "Vitamin B6 (g per 100g)" : "vit_B6",
                                  "Folate  total (g per 100g)" : "vit_B9",
                                  "Vitamin B-12 (g per 100g)" : "vit_B12",
                                  "Vitamin K (g per 100g)" : "vit_K"}

        nutrition_table_fields_order = ["Protein (N x 6.25) g per 100 g",
                                        "Total lipid (g per 100 g)",
                                        "Energy (kj) per 100 g",
                                        "Calcium (g per 100g)",
                                        "Iron (g per 100g)",
                                        "Magnesium (g per 100g)",
                                        "Phosphorus (g per 100g)",
                                        "Potassium (g per 100 g)",
                                        "Sodium (g per 100g)",
                                        "Zinc (g per 100g)",
                                        "Copper (g per 100g)",
                                        "Fluoride  F (g per 100g)",
                                        "Manganese (g per 100g)",
                                        "Selenium (g per 100g)",
                                        "Vitamin A (IU per 100g)",
                                        "Carotene  beta (g per 100g)",
                                        "Carotene  alpha (g per 100g)",
                                        "Vitamin E (alpha-tocopherol) g per 100g",
                                        "Cryptoxanthin  beta (g per 100g)",
                                        "Lycopene (g per 100g)",
                                        "Lutein + zeaxanthin (g per 100g)",
                                        "Tocopherol  beta (g per 100g)",
                                        "Tocopherol gamma (g per 100g)",
                                        "Tocopherol  Delta (g per 100g)",
                                        "Vitamin C (g per 100g)",
                                        "Thiamin (g per 100g)",
                                        "Riboflavin (g per 100g)",
                                        "Niacin (g per 100g)",
                                        "Pantothenic acid (g per 100 g)",
                                        "Vitamin B6 (g per 100g)",
                                        "Folate  total (g per 100g)",
                                        "Vitamin B-12 (g per 100g)",
                                        "Vitamin K (g per 100g)"]
        
        nutrition_table_field_id = "Id"

        nutrition_table_dict = raster_utils.get_lookup_from_csv(nutrition_table_uri,
                                                           nutrition_table_field_id)
    
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

    invest_crops = raster_utils.unique_raster_values_count(reclass_crop_cover_uri).keys()
    invest_crops.sort()
    if invest_crops[0] == 0:
        invest_crops.pop(0)

    def yield_op_closure(crop):
        def yield_op(cover, crop_yield):
            if crop_yield == nodata_float:
                return nodata_float
            elif cover != crop:
                return 0.0
            else:
                return crop_yield

        return yield_op

    
    for crop in invest_crops:
        LOGGER.debug("Separating out crop %i.", crop)
        crop_yield_uri = os.path.join(intermediate_uri, crop_yield_name % crop)
        raster_utils.vectorize_datasets([reclass_crop_cover_uri,
                                         os.path.join(raster_path,
                                                      raster_table_csv_dict[crop][raster_table_field_yield])],
                                        yield_op_closure(crop),
                                        crop_yield_uri,
                                        gdal_type_float,
                                        nodata_float,
                                        cell_size,
                                        "dataset",
                                        dataset_to_bound_index=0,
                                        assert_datasets_projected=False)

        statistics[crop] = {statistics_field_production : sum_uri(crop_yield_uri) * cell_size}
        #statistics[crop] = {statistics_field_production : 0}

    if args["calculate_nutrition"]:
        LOGGER.debug("Calculate nutrition.")

    if args["calculate_valuation"]:
        LOGGER.debug("Calculate valuation.")

    #create report
    report = open(report_uri, 'w')
    report.write("<HTML>")

    #cover summary
    report.write("<B>Crop Cover</B>")
    report.write("\n<TABLE BORDER=1>")
    row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3)
    row_html += ("<TD ALIGN=RIGHT>%s</TD>" * 2) + "</TR>"
    report.write(row_html % (reclass_table_field_key,
                             reclass_table_field_invest,
                             raster_table_field_short_name,
                             "Square Meters",
                             statistics_field_production))

    crop_counts = raster_utils.unique_raster_values_count(crop_cover_uri)
    crop_counts_keys = crop_counts.keys()
    crop_counts_keys.sort()

    if crop_counts_keys[0] == 0:
        crop_counts_keys.pop(0)

    for crop in crop_counts_keys:
        LOGGER.debug("Writing crop %i statistics to table.", crop)
        report.write(row_html % (str(crop),
                                 str(reclass_table[crop]),
                                 raster_table_csv_dict[reclass_table[crop]][raster_table_field_short_name],
                                 str(round(crop_counts[crop] * cell_size, 2)),
                                 str(round(statistics[crop][statistics_field_production],2))))

    report.write("\n</TABLE>")

    #nutrition summary
    if args["calculate_nutrition"]:
        LOGGER.info("Generating nutrition table.")

        report.write("\n<P><B>Nutrition</B>")

        report.write("\n<TABLE BORDER=1>")
        row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3)
        row_html += ("<TD ALIGN=RIGHT>%s</TD>" * len(nutrition_table_fields_order)) + "</TR>"
        header_row = [reclass_table_field_key,
                      reclass_table_field_invest,
                      raster_table_field_short_name]
        for nutrient in nutrition_table_fields_order:
            header_row.append(nutrition_table_fields[nutrient])
        report.write(row_html % tuple(header_row))

    
    report.write("\n</HTML>")
    report.close()
