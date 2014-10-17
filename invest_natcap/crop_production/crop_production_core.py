from osgeo import gdal, ogr, osr
import logging
from invest_natcap import raster_utils
import os
import sys
import numpy
import operator

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('crop_production_core')

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


def mosaic_by_attribute_uri(crop_uri,
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
        
    LOGGER.info("Mosaicing raster.")
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
        except (KeyError, ValueError):
            return nodata

    def __repr__(self):
        return repr(self.d)

def lookup_reclass_closure(lookup, field, nodata=-1):
    def lookup_reclass_op(crop, region):
        #LOGGER.debug([region, crop, field])
        try:
            return float(lookup["(%i, %i)" % (region, crop)][field])
        except (KeyError, ValueError):
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
            return self.key_error_value

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

def clip_project_align_dataset_uri(unclipped_uri, reference_uri, clipped_uri, align_method="nearest"):
    extent_uri = os.path.join(raster_utils.temporary_folder(), "tmp.shp")
    projected_extent_uri = os.path.join(raster_utils.temporary_folder(), "tmp.shp")
    clip_uri = raster_utils.temporary_filename()
    projected_clip_uri = raster_utils.temporary_filename()
    reference_align_uri = raster_utils.temporary_filename()

    input_wkt = gdal.Open(unclipped_uri).GetProjection()
    output_wkt = gdal.Open(reference_uri).GetProjection()
    cell_size = raster_utils.get_cell_size_from_uri(reference_uri)

    datasource_from_dataset_bounding_box_uri(reference_uri, extent_uri)
    raster_utils.reproject_datasource_uri(extent_uri, input_wkt, projected_extent_uri)    
    
    #clip
    raster_utils.clip_dataset_uri(unclipped_uri,
                                  projected_extent_uri,
                                  clip_uri,
                                  assert_projections=False)
    #project
    raster_utils.warp_reproject_dataset_uri(clip_uri,
                                            cell_size,
                                            output_wkt,
                                            align_method,
                                            projected_clip_uri)

    #align
    raster_utils.align_dataset_list([reference_uri,
                                     projected_clip_uri],
                                    [reference_align_uri,
                                     clipped_uri],
                                    [align_method, align_method],
                                    cell_size,
                                    "dataset",
                                    0,
                                    dataset_to_bound_index=0)
