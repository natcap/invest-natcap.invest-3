import logging

import os

from osgeo import gdal, ogr, osr
gdal.UseExceptions()

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('agriculture')

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
    

    intermediate_uri = os.path.join(workspace_dir, intermediate_dir)
    
    reclass_crop_cover_uri = os.path.join(intermediate_uri,
                                          reclass_name)
    
    report_uri = os.path.join(workspace_dir, report_name)
    
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

    #create report
    report = open(report_uri, 'w')
    report.write("<HTML>")

    report.write("<B>Crop Cover</B>")
    report.write("\n<TABLE BORDER=1>")
    row_html = "\n<TR>" + ("<TD ALIGN=CENTER>%s</TD>" * 3)+ "<TD ALIGN=RIGHT>%s</TD></TR>"
    report.write(row_html % (reclass_table_field_key,
                             reclass_table_field_invest,
                             raster_table_field_short_name,
                             "Square Meters"))

    crop_counts = raster_utils.unique_raster_values_count(crop_cover_uri)
    crop_counts_keys = crop_counts.keys()
    crop_counts_keys.sort()

    for crop in crop_counts_keys:
        report.write(row_html % (str(crop),
                                 str(reclass_table[crop]),
                                 raster_table_csv_dict[reclass_table[crop]][raster_table_field_short_name].title(),
                                 str(round(crop_counts[crop] * cell_size, 2))))

    report.write("\n</TABLE>")
    report.write("\n</HTML>")
    report.close()
