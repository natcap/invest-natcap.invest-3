"""
"""
from osgeo import gdal, ogr, osr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import copy
import os

import random

import operator
import math

import numpy

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
        """Constructor for ConstantOp class

        :param op: The callable operator
        :type op: <type 'function'>
        :param c: The list of constants
        :type c: list

        :return: instance of ConstantOp
        :rtype: <type 'instance'>
        """
        self.op = op
        self.c = c

    def __call__(self, *f):
        """Call to ConstantOp operator

        :param f: The paramters with which to call the operator
        :type f: list

        :return: return of the operator
        """
        return apply(self.op, f+self.c)

class DictOp:
    def __init__(self, d, op, *c):
        self.d = d
        self.op = op
        self.c = c

    def __getitem__(self, key):
        return apply(self.op, [self.d[key]] + self.c)

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

def sum_uri(dataset_uri, datasource_uri):
    """Wrapper call to raster_utils.aggregate_raster_values_uri to extract total

    :param dataset_uri: The uri for the input raster.
    :type dataset_uri: str

    :return: None
    :rtype: None
    """
    total = raster_utils.aggregate_raster_values_uri(dataset_uri, datasource_uri).total
    return total.__getitem__(total.keys().pop())

def sum_by_category_uri(category_uri, value_uri,categories=None):
    if categories == None:
        categories = raster_utils.unique_raster_values_count(category_uri).keys()

    category_src = gdal.Open(category_uri)
    category_band = category_src.GetRasterBand(1)

    values_src = gdal.Open(value_uri)
    values_band = values_src.GetRasterBand(1)

    category_sum = dict(zip(categories,[0]*len(categories)))
    for category in categories:
        for row_index in range(category_band.YSize):
            category_array = category_band.ReadAsArray(0, row_index, category_band.XSize, 1)[0]
            values_array = values_band.ReadAsArray(0, row_index, values_band.XSize, 1)[0]

            category_sum[category]+=numpy.sum(values_array[category_array == category])

    return category_sum

def alignment_check_uri(dataset_uri_list):
    dataset_uri = dataset_uri_list[0]
    dataset = gdal.Open(dataset_uri)
    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())

    base_n_rows = dataset.RasterYSize
    base_n_cols = dataset.RasterXSize
    base_linear_units = srs.GetLinearUnits()
    base_geotransform = dataset.GetGeoTransform()

    dataset = None

    for dataset_uri in dataset_uri_list[1:]:
        dataset = gdal.Open(dataset_uri)
        srs.SetProjection(dataset.GetProjection())

        LOGGER.debug("Checking linear units.")
        if srs.GetLinearUnits() != base_linear_units:
            msg = "Linear unit mismatch."
            LOGGER.error(msg)
            raise ValueError, msg

        LOGGER.debug("Checking origin, cell size, and rotation of pixels.")
        if dataset.GetGeoTransform() != base_geotransform:
            msg = "Geotransform mismatch."
            LOGGER.error(msg)
            raise ValueError, msg

        LOGGER.debug("Checking extents.")
        if dataset.RasterYSize != base_n_rows:
            msg = "Number or rows mismatch."
            LOGGER.error(msg)
            raise ValueError, msg

        if dataset.RasterXSize != base_n_cols:
            msg = "Number of columns mismatch."
            LOGGER.error(msg)
            raise ValueError, msg

        dataset = None

    return True

def execute(args):
    """Entry point for the blue carbon model.

    :param args["workspace_dir"]: The directory to hold output from a particular model run
    :type args["workspace_dir"]: str
    :param args["lulc_uri_1"]: The land use land cover raster for time 1.
    :type args["lulc_uri_1"]: str
    :param args["year_1"]: The year for the land use land cover raster for time 1.
    :type args["year_1"]: int
    :param args["lulc_uri_2"]: The land use land cover raster for time 2.
    :type args["lulc_uri_2"]: str
    :param args["year_2"]: The year for the land use land cover raster for time 2.
    :type args["year_2"]: int
    :param args["lulc_uri_3"]: The land use land cover raster for time 3.
    :type args["lulc_uri_3"]: str
    :param args["year_3"]: The year for the land use land cover raster for time 3.
    :type args["year_3"]: int
    :param args["lulc_uri_4"]: The land use land cover raster for time 4.
    :type args["lulc_uri_4"]: str
    :param args["year_4"]: The year for the land use land cover raster for time 4.
    :type args["year_4"]: int
    :param args["lulc_uri_5"]: The land use land cover raster for time 5.
    :type args["lulc_uri_5"]: str
    :param args["year_5"]: The year for the land use land cover raster for time 5.
    :type args["year_5"]: int

    """
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
    gdal_format = "GTiff"
    gdal_type_carbon = gdal.GDT_Float64
    nodata_default_int = -1
    nodata_default_float = -1
    gdal_type_identity_raster = gdal.GDT_Int16

    ##inputs parameters
    workspace_dir = args["workspace_dir"]
    analysis_year = args["analysis_year"]


    debug_log_file = open(os.path.join(workspace_dir, "debug.txt"), mode="w")
    debug_log = logging.StreamHandler(debug_log_file)
    debug_log.setFormatter(logging.Formatter(fmt='%(asctime)s %(message)s', datefmt="%M:%S"))
    LOGGER.addHandler(debug_log)

    #copy LULC for analysis year
    lulc_uri_dict[analysis_year]=lulc_uri_dict[lulc_years[-1]]

    #carbon pools table
    carbon_uri = args["carbon_pools_uri"]

    carbon_field_key = "Id"
    carbon_field_veg = "Veg Type"
    carbon_field_above = "Above"
    carbon_field_below = "Below"
    carbon_field_soil = "Soil"
    carbon_field_litter = "Litter"
    carbon_field_depth = "Soil Depth"
    carbon_acc_bio_field = "Bio_accum_rate"
    carbon_acc_soil_field = "Soil_accum_rate"

    #transition matrix
    trans_comment_uri = args["transition_matrix_uri"]

    #remove transition comment
    trans_uri = raster_utils.temporary_filename()

    trans_file = open(trans_uri, 'w')
    trans_file.write(open(trans_comment_uri).read().split("\n\n")[0])
    trans_file.close()

    trans_field_key = "Id"
    trans_acc = "Accumulation"

    #disturbance table
    dis_bio_csv_uri = args["biomass_disturbance_csv_uri"]
    dis_soil_csv_uri = args["soil_disturbance_csv_uri"]

    dis_field_key = "veg type"
    dis_field_veg_name = "veg name"

##    #accumulation table
##    acc_soil_csv_uri = args["soil_accumulation_csv_uri"]
##    acc_soil_field_key = "veg type"
##    acc_bio_csv_uri = args["biomass_accumulation_csv_uri"]
##    acc_bio_field_key = "veg type"

    #half-life table
    half_life_csv_uri = args["half_life_csv_uri"]
    half_life_field_key = "veg type"
    half_life_field_bio = "biomass"
    half_life_field_soil = "soil"

##    #valuation flags
##    private_valuation = args["private_valuation"]
##    social_valuation = args["social_valuation"]

    ##outputs
    extent_name = "extent.shp"
    report_name = "report.htm"
    blue_carbon_csv_name = "blue_carbon.csv"
    intermediate_dir = "intermediate"

    if not os.path.exists(os.path.join(workspace_dir, intermediate_dir)):
        os.makedirs(os.path.join(workspace_dir, intermediate_dir))

    #carbon pool file names
    above_name = os.path.join(intermediate_dir, "%i_stock_above.tif")
    below_name = os.path.join(intermediate_dir, "%i_stock_below.tif")
    soil_name = os.path.join(intermediate_dir, "%i_stock_soil.tif")
    litter_name = os.path.join(intermediate_dir, "%i_stock_litter.tif")
    bio_name = os.path.join(intermediate_dir, "%i_stock_bio.tif")
    carbon_name = "stock_%i.tif"

    veg_stock_bio_name = os.path.join(intermediate_dir, "%i_veg_%i_stock_biomass.tif")
    veg_stock_soil_name = os.path.join(intermediate_dir, "%i_veg_%i_stock_soil.tif")

    #carbon litter
    veg_litter_name = os.path.join(intermediate_dir, "%i_veg_%i_litter.tif")

    #carbon accumulation file names
    acc_soil_name = os.path.join(intermediate_dir, "%i_acc_soil.tif")
    acc_soil_co_name = os.path.join(intermediate_dir, "%i_%i_acc_soil_co.tif")
    acc_bio_name = os.path.join(intermediate_dir, "%i_acc_bio.tif")
    acc_bio_co_name = os.path.join(intermediate_dir, "%i_%i_acc_bio_co.tif")

    veg_acc_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_acc_bio.tif")
    veg_acc_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_acc_soil.tif")
    veg_dis_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_dis_bio.tif")
    veg_dis_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_dis_soil.tif")

    #carbon disturbance file names
    dis_bio_co_name = os.path.join(intermediate_dir, "%i_%i_dis_bio_co.tif")
    dis_soil_co_name = os.path.join(intermediate_dir, "%i_%i_dis_soil_co.tif")
    dis_bio_name = os.path.join(intermediate_dir, "%i_dis_bio.tif")
    dis_soil_name = os.path.join(intermediate_dir, "%i_dis_soil.tif")

    #half-life file names
    dis_bio_half_name = os.path.join(intermediate_dir, "%i_%i_dis_bio_half.tif")
    dis_bio_em_name = os.path.join(intermediate_dir, "%i_dis_bio_em.tif")
    dis_bio_adj_name = os.path.join(intermediate_dir, "%i_dis_bio_adj.tif")

    dis_soil_half_name = os.path.join(intermediate_dir, "%i_%i_dis_soil_half.tif")
    dis_soil_em_name = os.path.join(intermediate_dir, "%i_dis_soil_em.tif")
    dis_soil_adj_name = os.path.join(intermediate_dir, "%i_dis_soil_adj.tif")

    #adjusted carbon file names
    adj_above_name = os.path.join(intermediate_dir, "%i_adj_above.tif")
    adj_below_name = os.path.join(intermediate_dir, "%i_adj_below.tif")
    adj_bio_name = os.path.join(intermediate_dir, "%i_adj_bio.tif")
    adj_soil_name = os.path.join(intermediate_dir, "%i_adj_soil.tif")

    adj_dis_soil_veg_name = os.path.join(intermediate_dir, "%i_adj_dis_soil_veg_%i.tif")
    adj_dis_bio_veg_name = os.path.join(intermediate_dir, "%i_adj_dis_bio_veg_%i.tif")

    adj_undis_soil_veg_name = os.path.join(intermediate_dir, "%i_adj_undis_soil_veg_%i.tif")
    adj_undis_bio_veg_name = os.path.join(intermediate_dir, "%i_adj_undis_bio_veg_%i.tif")

    veg_adj_acc_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_acc_bio.tif")
    veg_adj_acc_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_acc_soil.tif")
    veg_adj_dis_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_dis_bio.tif")
    veg_adj_dis_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_dis_soil.tif")

    veg_adj_em_dis_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_em_dis_bio.tif")
    veg_adj_em_dis_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_adj_em_dis_soil.tif")

    #emission file names
    veg_mask_name = os.path.join(intermediate_dir, "%i_veg_mask_%i.tif")

    dis_bio_veg_name = os.path.join(intermediate_dir, "%i_dis_bio_veg_%i.tif")
    dis_soil_veg_name = os.path.join(intermediate_dir, "%i_dis_soil_veg_%i.tif")

    undis_bio_veg_name = os.path.join(intermediate_dir, "%i_undis_bio_veg_%i.tif")
    undis_soil_veg_name = os.path.join(intermediate_dir, "%i_undis_soil_veg_%i.tif")

    em_soil_veg_name = os.path.join(intermediate_dir, "%i_%i_em_soil_veg_%i.tif")
    em_bio_veg_name = os.path.join(intermediate_dir, "%i_%i_em_bio_veg_%i.tif")

    veg_em_bio_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_em_bio.tif")
    veg_em_soil_name = os.path.join(intermediate_dir, "%i_%i_veg_%i_em_soil.tif")

    em_name = os.path.join(intermediate_dir, "%i_%i_em.tif")

    #net file names
    net_dis_bio_veg_name = os.path.join(intermediate_dir, "%i_net_dis_bio_veg_%i.tif")
    net_dis_soil_veg_name = os.path.join(intermediate_dir, "%i_net_dis_soil_veg_%i.tif")

    #totals
    this_total_acc_soil_name = os.path.join(intermediate_dir, "%i_%i_soil_acc.tif")
    this_total_acc_bio_name = os.path.join(intermediate_dir, "%i_%i_bio_acc.tif")
    this_total_dis_soil_name = os.path.join(intermediate_dir, "%i_%i_soil_dis.tif")
    this_total_dis_bio_name = os.path.join(intermediate_dir, "%i_%i_bio_dis.tif")
    net_sequestration_name = "sequest_%i_%i.tif"
    gain_name = "gain_%i_%i.tif"
    loss_name = "loss_%i_%i.tif"

    #uri

    extent_uri = os.path.join(workspace_dir, extent_name)
    report_uri = os.path.join(workspace_dir, report_name)
    blue_carbon_csv_uri = os.path.join(workspace_dir, blue_carbon_csv_name)

    ##process inputs
    #load tables from files
##    acc_soil = raster_utils.get_lookup_from_csv(acc_soil_csv_uri, acc_soil_field_key)
##    acc_bio = raster_utils.get_lookup_from_csv(acc_bio_csv_uri, acc_bio_field_key)

    dis_bio = raster_utils.get_lookup_from_csv(dis_bio_csv_uri, dis_field_key)
    #adding accumulation value to disturbance table
    for k in dis_bio:
        dis_bio[k][trans_acc] = 0.0

    dis_soil = raster_utils.get_lookup_from_csv(dis_soil_csv_uri, dis_field_key)
    #adding accumulation values to disturbance table
    for k in dis_soil:
        dis_soil[k][trans_acc] = 0.0
    

    trans = raster_utils.get_lookup_from_csv(trans_uri, trans_field_key)
    carbon = raster_utils.get_lookup_from_csv(carbon_uri, carbon_field_key)

    class InfiniteDict:
        def __init__(self, k, v):
            self.d = {k : v}

        def __getitem__(self, k):
            try:
                return self.d[k]
            except KeyError:
                return 0.0

        def __repr__(self):
            return repr(self.d)

    #constructing accumulation tables from carbon table
    acc_soil = {}
    for k in carbon:
        acc_soil[k] = InfiniteDict(trans_acc, carbon[k][carbon_acc_soil_field])

    acc_bio = {}
    for k in carbon:
        acc_bio[k] = InfiniteDict(trans_acc, carbon[k][carbon_acc_bio_field])

    half_life = raster_utils.get_lookup_from_csv(half_life_csv_uri, half_life_field_key)
    print half_life

    #validate disturbance and accumulation tables
    change_types = set()
    for k1 in trans:
        for k2 in trans:
            change_types.add(trans[k1][str(k2)])

##    change_columns = set(acc_soil[random.choice(list(acc_soil.keys()))].keys())
##    if change_columns.issuperset(change_types):
##        LOGGER.debug("Soil accumulation table valid.")
##    else:
##        msg = "The transition matrix contains the following value(s) not in soil the accumulation table: %s", str(change_types.difference(change_columns))
##        LOGGER.error(msg)
##        raise ValueError, msg
##
##    change_columns = set(dis_soil[random.choice(list(dis_soil.keys()))].keys())
##    if change_columns.issuperset(change_types):
##        LOGGER.debug("Soil disturbance table valid.")
##    else:
##        msg = "The transition matrix contains the following value(s) not in the soil disturbance table: %s", str(change_types.difference(change_columns))
##        LOGGER.error(msg)
##        raise ValueError, msg
##
##    change_columns = set(acc_bio[random.choice(list(acc_bio.keys()))].keys())
##    if change_columns.issuperset(change_types):
##        LOGGER.debug("Biomass accumulation table valid.")
##    else:
##        msg = "The transition matrix contains the following value(s) not in the biomass accumulation table: %s", str(change_types.difference(change_columns))
##        LOGGER.error(msg)
##        raise ValueError, msg
##
##    change_columns = set(dis_bio[random.choice(list(dis_bio.keys()))].keys())
##    if change_columns.issuperset(change_types):
##        LOGGER.debug("Biomass disturbance table valid.")
##    else:
##        msg = "The transition matrix contains the following value(s) not in the biomass disturbance table: %s", str(change_types.difference(change_columns))
##        LOGGER.error(msg)
##        raise ValueError, msg

    #validating data
    nodata_lulc = set([raster_utils.get_nodata_from_uri(lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(nodata_lulc) == 1:
        LOGGER.debug("All rasters have the same nodata value.")
        nodata_lulc = nodata_lulc.pop()
    else:
        msg = "All rasters must have the same nodata value."
        LOGGER.error(msg)
        raise ValueError, msg

    cell_size = set([raster_utils.get_cell_size_from_uri(lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(cell_size) == 1:
        LOGGER.debug("All rasters have the same cell size.")
        cell_size = cell_size.pop()
    else:
        msg = "All rasters must have the same cell size."
        LOGGER.error(msg)
        raise ValueError, msg

    LOGGER.debug("Checking alignment.")
    try:
        alignment_check_uri([lulc_uri_dict[k] for k in lulc_uri_dict])
    except ValueError, msg:
        LOGGER.error("Alignment check FAILED.")
        LOGGER.error(msg)
        raise ValueError, msg

    #construct dictionaries for single parameter lookups
    conversion = (raster_utils.get_cell_size_from_uri(lulc_uri_dict[lulc_years[0]]) ** 2) / 10000.0 #convert to Ha

    LOGGER.debug("Cell size is %s hectacres.", conversion)

    veg_dict = dict([(k, int(carbon[k][carbon_field_veg])) for k in carbon])

    veg_type_list = list(set([veg_dict[k] for k in veg_dict]))

    ##create carbon field dictionary
    veg_field_dict = {}
    for veg_type in veg_type_list:
        veg_field_dict[veg_type] = {}
        for field in [carbon_field_above, carbon_field_below, carbon_field_litter, carbon_field_soil]:
            veg_field_dict[veg_type][field] = {}
            for k in carbon:
                if int(carbon[k][carbon_field_veg]) == veg_type:
                    veg_field_dict[veg_type][field][k] = float(carbon[k][field]) * conversion
                else:
                    veg_field_dict[veg_type][field][k] = 0.0

    #add biomass to carbon field
    carbon_field_bio = "bio"
    for veg_type in veg_type_list:
        veg_field_dict[veg_type][carbon_field_bio] = {}
        for k in carbon:
            veg_field_dict[veg_type][carbon_field_bio][k] = veg_field_dict[veg_type][carbon_field_below][k] + veg_field_dict[veg_type][carbon_field_above][k]

    ##create transition field dictionary
    acc_soil_name = "acc_soil"
    acc_bio_name = "acc_bio"
    dis_bio_name = "dis_bio"
    dis_soil_name = "dis_soil"

    #accumulation
    #print acc_soil
    veg_trans_acc_dict = {}
    for veg_type in veg_type_list:
        veg_trans_acc_dict[veg_type] = {}
        for component, component_dict in [(acc_soil_name, acc_soil),
                                          (acc_bio_name, acc_bio)]:
            veg_trans_acc_dict[veg_type][component] = {}
            for original_lulc in trans:
                veg_trans_acc_dict[veg_type][component][original_lulc] = {}
                for transition_lulc in trans:
                    if int(carbon[original_lulc][carbon_field_veg]) == veg_type:
                        veg_trans_acc_dict[veg_type][component][(original_lulc, transition_lulc)] = component_dict[transition_lulc][trans[original_lulc][str(transition_lulc)]] * conversion
                    else:
                        veg_trans_acc_dict[veg_type][component][(original_lulc, transition_lulc)] = 0.0

    #disturbance
    trans_dis_dict = {}
    for component, component_dict in [(dis_bio_name, dis_bio),
                                      (dis_soil_name, dis_soil)]:
        trans_dis_dict[component] = {}
        for original_lulc in trans:
            for transition_lulc in trans:
                trans_dis_dict[component][(original_lulc, transition_lulc)] = component_dict[carbon[original_lulc][carbon_field_veg]][trans[original_lulc][str(transition_lulc)]]

    ##vectorize datasets operations
    #standard ops
    def add_op(*values):
        if nodata_default_int in values:
            return nodata_default_int
        return reduce(operator.add, values)

    def sub_op(*values):
        if nodata_default_int in values:
            return nodata_default_int
        return reduce(operator.sub, values)

    def mul_op(*values):
        if nodata_default_int in values:
            return nodata_default_int
        return reduce(operator.mul,values)

    #custom ops
    def acc_bio_op_closure(veg_type, t):
        def acc_bio_co_op(original_lulc, transition_lulc):
            if nodata_lulc in [original_lulc, transition_lulc]:
                return nodata_default_float
            return veg_trans_acc_dict[veg_type][acc_bio_name][(int(original_lulc), int(transition_lulc))] * t

        return acc_bio_co_op

    def acc_soil_op_closure(veg_type, t):
        def acc_soil_co_op(original_lulc, transition_lulc):
            if nodata_lulc in [original_lulc, transition_lulc]:
                return nodata_default_float
            return veg_trans_acc_dict[veg_type][acc_soil_name][(int(original_lulc), int(transition_lulc))] * t

        return acc_soil_co_op

    def dis_bio_op(carbon_base, original_lulc, transition_lulc):
        if nodata_lulc in [carbon_base, original_lulc, transition_lulc]:
            return nodata_default_float
        return carbon_base * trans_dis_dict[dis_bio_name][(int(original_lulc), int(transition_lulc))]

    def dis_soil_op(carbon_base, original_lulc, transition_lulc):
        if nodata_lulc in [carbon_base, original_lulc, transition_lulc]:
            return nodata_default_float
        return carbon_base * trans_dis_dict[dis_soil_name][(int(original_lulc), int(transition_lulc))]

    def adj_op(base, acc, dis):
        if nodata_default_float in [base, acc, dis]:
            return nodata_default_float
        else:
            return base + acc - dis

    def net_sequestration_op(bio_acc, bio_dis, soil_acc, soil_dis):
        if nodata_default_float in [bio_acc, bio_dis, soil_acc, soil_dis]:
            return nodata_default_float
        else:
            return ((bio_acc + soil_acc) - (bio_dis + soil_dis))

    def veg_adj_op(base, adj, mask):
        if nodata_default_float in [base, adj, mask]:
            return nodata_default_float
        else:
            return base + (adj * mask)

    def vectorize_carbon_datasets(dataset_uri_list, dataset_pixel_op, dataset_out_uri):
        raster_utils.vectorize_datasets(dataset_uri_list,
                                        dataset_pixel_op,
                                        dataset_out_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")

    def half_life_op_closure(veg_type, half_life_field, alpha_t):
        def h_l_op(c):
            if c is nodata_default_float:
                return c
            alpha = half_life[veg_type][half_life_field]
            #print repr(alpha_t), repr(alpha), repr(c)
            try:
                h_l = alpha_t/float(alpha)
                resid = 0.5 ** h_l
                coeff = 1 - resid
                r = coeff * c
##                if c > 0:
##                    print repr(c), repr(h_l), repr(resid), repr(coeff), repr(r)
                return r
            except ValueError:
                #return 0 if alpha is None
                return 0
        return h_l_op

    LOGGER.info("Running analysis.")
    ##calculate stock carbon values
    this_year = lulc_years[0]
    this_uri = lulc_uri_dict[this_year]

##    #add reclass entry for nodata
##    above_dict[int(nodata_lulc)] = nodata_default_float
##    below_dict[int(nodata_lulc)] = nodata_default_float
##    soil_dict[int(nodata_lulc)] = nodata_default_float
##    litter_dict[int(nodata_lulc)] = nodata_default_float
##    depth_dict[int(nodata_lulc)] = nodata_default_float

    LOGGER.info("Calculating stock carbon values.")
    #local variable names
    this_above_uri = os.path.join(workspace_dir, above_name % this_year)
    this_below_uri = os.path.join(workspace_dir, below_name % this_year)
    this_soil_uri = os.path.join(workspace_dir, soil_name % this_year)
    this_litter_uri = os.path.join(workspace_dir, litter_name % this_year)
    this_bio_uri = os.path.join(workspace_dir, bio_name % this_year)

    #create vegetation specific stock values for biomass and soil
    base_veg_acc_bio = "base_veg_acc_bio"
    base_veg_acc_soil = "base_veg_acc_soil"
    base_veg_dis_bio = "base_veg_dis_bio"
    base_veg_dis_soil = "base_veg_dis_soil"
    veg_base_uri_dict = {}

    #creating zero-fill raster for initial disturbed carbon
    zero_raster_uri = os.path.join(workspace_dir, os.path.join(intermediate_dir, "zeros.tif"))
    raster_utils.new_raster_from_base_uri(this_uri,
                                          zero_raster_uri,
                                          gdal_format,
                                          nodata_default_int,
                                          gdal_type_identity_raster,
                                          fill_value = 0)

    for veg_type in veg_type_list:
        veg_base_uri_dict[veg_type] = {}

        this_veg_stock_soil_uri = os.path.join(workspace_dir, veg_stock_soil_name % (this_year, veg_type))
        this_veg_stock_bio_uri = os.path.join(workspace_dir, veg_stock_bio_name % (this_year, veg_type))

        raster_utils.reclassify_dataset_uri(this_uri,
                                            veg_field_dict[veg_type][carbon_field_bio],
                                            this_veg_stock_bio_uri,
                                            gdal_type_carbon,
                                            nodata_default_float,
                                            exception_flag = "values_required")

        raster_utils.reclassify_dataset_uri(this_uri,
                                            veg_field_dict[veg_type][carbon_field_soil],
                                            this_veg_stock_soil_uri,
                                            gdal_type_carbon,
                                            nodata_default_float,
                                            exception_flag = "values_required")

        veg_base_uri_dict[veg_type][base_veg_acc_bio] = this_veg_stock_bio_uri
        veg_base_uri_dict[veg_type][base_veg_acc_soil] = this_veg_stock_soil_uri
        veg_base_uri_dict[veg_type][base_veg_dis_bio] = zero_raster_uri
        veg_base_uri_dict[veg_type][base_veg_dis_soil] = zero_raster_uri


    ##loop over lulc years

    #create extent shapefile
    datasource_from_dataset_bounding_box_uri(this_uri, extent_uri)        
    #print veg_trans_acc_dict
    totals = {}
    stock_uri_dict = {}    
    for this_year, next_year in zip(lulc_years, lulc_years[1:]+[analysis_year]):
        this_total_carbon_uri = os.path.join(workspace_dir, carbon_name % this_year)
        this_total_carbon_uri_list = []

        this_total_acc_soil_uri = os.path.join(workspace_dir, this_total_acc_soil_name % (this_year, next_year))
        this_total_acc_bio_uri = os.path.join(workspace_dir, this_total_acc_bio_name % (this_year, next_year))
        this_total_dis_soil_uri = os.path.join(workspace_dir, this_total_dis_soil_name % (this_year, next_year))
        this_total_dis_bio_uri = os.path.join(workspace_dir, this_total_dis_bio_name % (this_year, next_year))
        this_total_em_uri = os.path.join(workspace_dir, em_name % (this_year, next_year))

        veg_acc_bio_uri_list = []
        veg_acc_soil_uri_list = []
        veg_dis_bio_uri_list = []
        veg_dis_soil_uri_list = []
        veg_seq_uri_list = []
##        em_uri_list = []
    
        totals[this_year] = {}

        LOGGER.info("Transition from %i to %i.", this_year, next_year)
        this_uri = lulc_uri_dict[this_year]
        next_uri = lulc_uri_dict[next_year]

        t = next_year - this_year

        for veg_type in veg_type_list:
            totals[this_year][veg_type] = {}
            
            LOGGER.info("Processing vegetation type %i.", veg_type)
            #litter URI's
            this_veg_litter_uri = os.path.join(workspace_dir, veg_litter_name % (this_year, veg_type))
            
            #disturbance and accumulation URI's
            this_veg_acc_bio_uri = os.path.join(workspace_dir, veg_acc_bio_name % (this_year, next_year, veg_type))
            this_veg_acc_soil_uri = os.path.join(workspace_dir, veg_acc_soil_name % (this_year, next_year, veg_type))
            this_veg_dis_bio_uri = os.path.join(workspace_dir, veg_dis_bio_name % (this_year, next_year, veg_type))
            this_veg_dis_soil_uri = os.path.join(workspace_dir, veg_dis_soil_name % (this_year, next_year, veg_type))

            #transition adjusted URI's
            this_veg_adj_acc_bio_uri = os.path.join(workspace_dir, veg_adj_acc_bio_name % (this_year, next_year, veg_type))
            this_veg_adj_acc_soil_uri = os.path.join(workspace_dir, veg_adj_acc_soil_name % (this_year, next_year, veg_type))
            this_veg_adj_dis_bio_uri = os.path.join(workspace_dir, veg_adj_dis_bio_name % (this_year, next_year, veg_type))
            this_veg_adj_dis_soil_uri = os.path.join(workspace_dir, veg_adj_dis_soil_name % (this_year, next_year, veg_type))

            #emission URI's
            this_veg_em_bio_uri = os.path.join(workspace_dir, veg_em_bio_name  % (this_year, next_year, veg_type))
            this_veg_em_soil_uri = os.path.join(workspace_dir, veg_em_soil_name  % (this_year, next_year, veg_type))

            #emission adjusted URI's
            this_veg_adj_em_dis_bio_uri = os.path.join(workspace_dir, veg_adj_em_dis_bio_name  % (this_year, next_year, veg_type))
            this_veg_adj_em_dis_soil_uri = os.path.join(workspace_dir, veg_adj_em_dis_soil_name  % (this_year, next_year, veg_type))

            ##litter
            raster_utils.reclassify_dataset_uri(this_uri,
                                                veg_field_dict[veg_type][carbon_field_litter],
                                                this_veg_litter_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                exception_flag = "values_required")

            ##accumulation
            #biomass accumulation
            vectorize_carbon_datasets([this_uri, next_uri],
                                       acc_bio_op_closure(veg_type, t),
                                       this_veg_acc_bio_uri)

            #soil accumulation
            vectorize_carbon_datasets([this_uri, next_uri],
                                       acc_soil_op_closure(veg_type, t),
                                       this_veg_acc_soil_uri)

            ##disturbance
            #biomass disturbance
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_acc_bio], this_uri, next_uri],
                                      dis_bio_op,
                                      this_veg_dis_bio_uri)

            #soil disturbance
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_acc_soil], this_uri, next_uri],
                                      dis_soil_op,
                                      this_veg_dis_soil_uri)

            ##transition adjustments
            #transition adjusted undisturbed biomass
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_acc_bio], this_veg_acc_bio_uri, this_veg_dis_bio_uri],
                                      adj_op,
                                      this_veg_adj_acc_bio_uri)

            #transition adjusted undisturbed soil
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_acc_soil], this_veg_acc_soil_uri, this_veg_dis_soil_uri],
                                      adj_op,
                                      this_veg_adj_acc_soil_uri)

            #transition adjusted disturbed biomass
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_dis_bio], this_veg_dis_bio_uri],
                                      add_op,
                                      this_veg_adj_dis_bio_uri)

            #transition adjusted disturbed soil
            vectorize_carbon_datasets([veg_base_uri_dict[veg_type][base_veg_dis_soil], this_veg_dis_soil_uri],
                                      add_op,
                                      this_veg_adj_dis_soil_uri)

            ##emissions
            #biomass emissions
            vectorize_carbon_datasets([this_veg_adj_dis_bio_uri],
                                      half_life_op_closure(veg_type, half_life_field_bio, t),
                                      this_veg_em_bio_uri)

            #soil emissions
            vectorize_carbon_datasets([this_veg_adj_dis_soil_uri],
                                      half_life_op_closure(veg_type, half_life_field_soil, t),
                                      this_veg_em_soil_uri)

##            em_uri_list = []
##            em_uri_list.append(this_veg_em_bio_uri)
##            em_uri_list.append(this_veg_em_soil_uri)

            ##emissions adjustment
            #emissions adjusted disturbed biomass
            vectorize_carbon_datasets([this_veg_adj_dis_bio_uri, this_veg_em_bio_uri],
                                      sub_op,
                                      this_veg_adj_em_dis_bio_uri)

            #emissions adjusted disturbed soil
            vectorize_carbon_datasets([this_veg_adj_dis_soil_uri, this_veg_em_soil_uri],
                                      sub_op,
                                      this_veg_adj_em_dis_soil_uri)

            #totals
##            this_total_carbon_uri_list.append(this_veg_adj_acc_bio_uri)
##            this_total_carbon_uri_list.append(this_veg_adj_acc_soil_uri)
##            this_total_carbon_uri_list.append(this_veg_litter_uri)
            
            veg_acc_bio_uri_list.append(this_veg_acc_bio_uri)
            veg_acc_soil_uri_list.append(this_veg_acc_soil_uri)
            veg_dis_bio_uri_list.append(this_veg_dis_bio_uri)
            veg_dis_soil_uri_list.append(this_veg_dis_soil_uri)
            
            for name, uri in [(veg_acc_bio_name, this_veg_acc_bio_uri),
                              (veg_acc_soil_name, this_veg_acc_soil_uri),
                              (veg_dis_bio_name, this_veg_dis_bio_uri),
                              (veg_dis_soil_name, this_veg_dis_soil_uri),
                              (veg_adj_acc_bio_name, this_veg_adj_acc_bio_uri),
                              (veg_adj_acc_soil_name, this_veg_adj_acc_soil_uri),
                              (veg_adj_dis_bio_name, this_veg_adj_dis_bio_uri),
                              (veg_adj_dis_soil_name, this_veg_adj_dis_soil_uri),
                              (veg_em_bio_name, this_veg_em_bio_uri),
                              (veg_em_soil_name, this_veg_em_soil_uri),
                              (veg_adj_em_dis_bio_name, this_veg_adj_em_dis_bio_uri),
                              (veg_adj_em_dis_soil_name, this_veg_adj_em_dis_soil_uri)]:
                totals[this_year][veg_type][name] = sum_uri(uri, extent_uri)
            
            ##switch base carbon rasters
            this_total_carbon_uri_list.append(veg_base_uri_dict[veg_type][base_veg_acc_bio])
            this_total_carbon_uri_list.append(veg_base_uri_dict[veg_type][base_veg_acc_soil])
            this_total_carbon_uri_list.append(this_veg_litter_uri)
                
            veg_base_uri_dict[veg_type][base_veg_acc_bio] = this_veg_adj_acc_bio_uri
            veg_base_uri_dict[veg_type][base_veg_acc_soil] = this_veg_adj_acc_soil_uri
            veg_base_uri_dict[veg_type][base_veg_dis_bio] = this_veg_adj_em_dis_bio_uri
            veg_base_uri_dict[veg_type][base_veg_dis_soil] = this_veg_adj_em_dis_soil_uri

        vectorize_carbon_datasets(this_total_carbon_uri_list,
                                  add_op,
                                  this_total_carbon_uri)

        stock_uri_dict[this_year] = this_total_carbon_uri
        
        ##carbon totals
##        vectorize_carbon_datasets(em_uri_list,
##                                  add_op,
##                                  this_total_em_uri)
        
        vectorize_carbon_datasets(veg_acc_bio_uri_list,
                                  add_op,
                                  this_total_acc_bio_uri)

        vectorize_carbon_datasets(veg_acc_soil_uri_list,
                                  add_op,
                                  this_total_acc_soil_uri)

        vectorize_carbon_datasets(veg_dis_bio_uri_list,
                                  add_op,
                                  this_total_dis_bio_uri)

        vectorize_carbon_datasets(veg_dis_soil_uri_list,
                                  add_op,
                                  this_total_dis_soil_uri)

    def pos_op(v):
        if v is nodata_default_float:
            return v
        elif v >= 0:
            return v
        else:
            return 0

    def neg_op(v):
        if v is nodata_default_float:
            return v
        elif v < 0:
            return v * -1
        else:
            return 0
        
    for i, this_year in enumerate(lulc_years[:-1]):
        for next_year in lulc_years[i+1:]:
            LOGGER.info("Calculating sequestration from %i to %i.", this_year, next_year)
            total_seq_uri = os.path.join(workspace_dir, net_sequestration_name % (this_year, next_year))
            gain_uri = os.path.join(workspace_dir, gain_name % (this_year, next_year))
            loss_uri = os.path.join(workspace_dir, loss_name % (this_year, next_year))
            
            stock_uri_list = [stock_uri_dict[next_year],
                              stock_uri_dict[this_year]]
            vectorize_carbon_datasets(stock_uri_list,
                                      sub_op,
                                      total_seq_uri)

            vectorize_carbon_datasets([total_seq_uri],
                                      pos_op,
                                      gain_uri)

            vectorize_carbon_datasets([total_seq_uri],
                                      neg_op,
                                      loss_uri)
            

    ##generate csv
    #open csv
    csv = open(blue_carbon_csv_uri, 'w')

    header = ["Year"]
    for name, label in [(veg_acc_bio_name, "Acc Bio"),
                      (veg_acc_soil_name, "Acc Soil"),
                      (veg_dis_bio_name, "Dis Bio"),
                      (veg_dis_soil_name, "Dis Soil"),
##                      (veg_adj_acc_bio_name, this_veg_adj_acc_bio_uri),
##                      (veg_adj_acc_soil_name, this_veg_adj_acc_soil_uri),
##                      (veg_adj_dis_bio_name, this_veg_adj_dis_bio_uri),
##                      (veg_adj_dis_soil_name, this_veg_adj_dis_soil_uri),
                      (veg_em_bio_name, "Em Bio"),
                      (veg_em_soil_name, "Em Soil")]:
##                      (veg_adj_em_dis_bio_name, this_veg_adj_em_dis_bio_uri),
##                      (veg_adj_em_dis_soil_name, this_veg_adj_em_dis_soil_uri)]:
        for veg_type in veg_type_list:
            header.append(label + (" Veg %i" % veg_type))

    csv.write(",".join(header))


    for year in lulc_years:
        row = [str(year)]
        for name, label in [(veg_acc_bio_name, "Acc Bio"),
                          (veg_acc_soil_name, "Acc Soil"),
                          (veg_dis_bio_name, "Dis Bio"),
                          (veg_dis_soil_name, "Dis Soil"),
    ##                      (veg_adj_acc_bio_name, this_veg_adj_acc_bio_uri),
    ##                      (veg_adj_acc_soil_name, this_veg_adj_acc_soil_uri),
    ##                      (veg_adj_dis_bio_name, this_veg_adj_dis_bio_uri),
    ##                      (veg_adj_dis_soil_name, this_veg_adj_dis_soil_uri),
                          (veg_em_bio_name, "Em Bio"),
                          (veg_em_soil_name, "Em Soil")]:
    ##                      (veg_adj_em_dis_bio_name, this_veg_adj_em_dis_bio_uri),
    ##                      (veg_adj_em_dis_soil_name, this_veg_adj_em_dis_soil_uri)]:
            for veg_type in veg_type_list:
                row.append(str(totals[year][veg_type][name]))
        csv.write("\n" + ",".join(row))

    csv.close()
            


    #open report
    report = open(report_uri, 'w')
    report.write("<HTML><TITLE>InVEST - Blue Carbon Report</TITLE><BODY>")

    #totals
    report.write("<B>LULC/Year Input Summary</B>")
    column_name_list = ["Start-End Year",
                        "Biomass Accumulation",                        
                        "Soil Accumulation",
                        "Biomass Disturbance",                        
                        "Soil Disturbance",
                        "Emissions (Biomass)",
                        "Emissions (Soil)"]
   
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))

    for this_year in lulc_years:
        row = [str(this_year) + "-"]

        for name in [veg_acc_bio_name,
                     veg_dis_bio_name,
                     veg_acc_soil_name,
                     veg_dis_soil_name,
                     veg_em_bio_name,
                     veg_em_soil_name]:

            total = 0
            for veg_type in veg_type_list:
                total += totals[this_year][veg_type][name]

            row.append(total)
        row.append(row[1]+row[3]-row[5]-row[6])        

        report.write("<TR><TD>%s</TD></TR>" % "</TD><TD>".join([str(value) for value in [row[0],
                                                                                         row[1],
                                                                                         row[3],
                                                                                         row[2],
                                                                                         row[4],
                                                                                         row[5],
                                                                                         row[6]]]))

    report.write("\n</TABLE>")

##    #emissions
##    report.write("<P><P><B>Carbon Lost/Gained</B>")
##
##    column_name_list = ["Year","Gained","Lost","Sequestration"]
##
##    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))
##    
##    for this_year in range(lulc_years[0],analysis_year+1):
##        if this_year in lulc_years: # + [analysis_year]:
##            row = ["<B>%i</B>" % this_year]
##            start_year = this_year
##            stop_year = (lulc_years + [analysis_year])[lulc_years.index(start_year)+1]
##            span = float(stop_year - start_year)
##            acc_total = 0
##            for veg_type in veg_type_list:
##                acc_total += totals[this_year][veg_type][veg_acc_bio_name] + totals[this_year][veg_type][veg_acc_soil_name]
##        else:
##            row = [this_year]
##                
##        em_total = 0
##        this_span = stop_year - this_year
##        for veg_type in veg_type_list:
##            try:
##                bio_alpha = float(half_life[veg_type][half_life_field_bio])
##
##                bio_start_co = 1 - (0.5 ** (-1 * ((span - this_span)/ bio_alpha)))
##                bio_stop_co = 1 - (0.5 ** (-1 * ((span - (this_span - 1))/ bio_alpha)))
##                bio_co = bio_stop_co - bio_start_co
##
##                em_total += totals[start_year][veg_type][veg_em_bio_name] * bio_co
##
##            except ValueError:
##                pass
##
##            try:
##                soil_alpha = float(half_life[veg_type][half_life_field_soil])
##
##                soil_start_co = 1 - (0.5 ** (-1 * ((span - this_span)/ soil_alpha)))
##                soil_stop_co = 1 - (0.5 ** (-1 * ((span - (this_span - 1))/ soil_alpha)))
##                soil_co = soil_stop_co - soil_start_co
##
##                em_total += totals[start_year][veg_type][veg_em_soil_name] * soil_co
##                
##            except ValueError:
##                pass
##            
##        row.extend([acc_total / span, em_total])
##        row.append(row[-2]-row[-1])
##
##        report.write("<TR><TD>%s</TD></TR>" % "</TD><TD>".join([str(value) for value in row]))
##
##    report.write("\n</TABLE>")


    #input CSVs
    report.write("<P><P><B>Input Tables</B><P><P>")
    for csv_uri, name in [(carbon_uri, "Stock Carbon"),
                          (trans_uri, "Transition Matrix"),
                          (dis_bio_csv_uri, "Biomass Disturbance"),
                          (dis_soil_csv_uri, "Soil Disturbance"),
                          #(acc_bio_csv_uri, "Biomass Accumulation"),
                          #(acc_soil_csv_uri, "Soil Accumulation"),
                          (half_life_csv_uri, "Decay Rates (Half-Life)")]:
        table = "<TABLE BORDER=1><TR><TD>" + open(csv_uri).read().strip().replace(",","</TD><TD>").replace("\n","</TD></TR><TR><TD>") + "</TD></TR></TABLE>"

        report.write("<P><P><B>%s</B>" % name)
        report.write(table)
    
    #close report
    report.write("\n</BODY></HTML>")
    report.close()

##
##    ##clean up
    driver = gdal.GetDriverByName('GTiff')
    driver.Delete(zero_raster_uri)
##    for year in lulc_years[1:]:
##        LOGGER.debug("Cleaning up intermediates for year %i." % year)
##        driver.Delete(os.path.join(workspace_dir, above_name % year))
##        driver.Delete(os.path.join(workspace_dir, below_name % year))
##        driver.Delete(os.path.join(workspace_dir, soil_name % year))
##        #driver.Delete(os.path.join(workspace_dir, litter_name % year))
##        driver.Delete(os.path.join(workspace_dir, bio_name % year))
##        #driver.Delete(os.path.join(workspace_dir, carbon_name % year))
##
##    for uri in acc_soil_uri_list+dis_soil_uri_list+dis_bio_uri_list:
##        driver.Delete(uri)
##
##    datasource = ogr.Open(extent_uri, 1)
##    datasource.DeleteLayer(0)
##    datasource = None

##    debug_log.flush()
##    debug_log = None
##    debug_log_file.close()
