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

    #transition matrix
    trans_uri = args["transition_matrix_uri"]

    trans_field_key = "Id"

    #disturbance table
    dis_bio_csv_uri = args["biomass_disturbance_csv_uri"]
    dis_soil_csv_uri = args["soil_disturbance_csv_uri"]

    dis_field_key = "veg type"
    dis_field_veg_name = "veg name"

    #accumulation table
    acc_soil_csv_uri = args["soil_accumulation_csv_uri"]
    acc_soil_field_key = "veg type"
    acc_bio_csv_uri = args["biomass_accumulation_csv_uri"]
    acc_bio_field_key = "veg type"    

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
    intermediate_dir = "intermediate"

    if not os.path.exists(os.path.join(workspace_dir, intermediate_dir)):
        os.makedirs(os.path.join(workspace_dir, intermediate_dir))
    
    #carbon pool file names
    above_name = os.path.join(intermediate_dir, "%i_stock_above.tif")
    below_name = os.path.join(intermediate_dir, "%i_stock_below.tif")
    soil_name = os.path.join(intermediate_dir, "%i_stock_soil.tif")
    litter_name = os.path.join(intermediate_dir, "%i_stock_litter.tif")
    bio_name = os.path.join(intermediate_dir, "%i_stock_bio.tif")
    carbon_name = "%i_total.tif"

    #carbon accumulation file names
    acc_soil_name = os.path.join(intermediate_dir, "%i_acc_soil.tif")
    acc_soil_co_name = os.path.join(intermediate_dir, "%i_%i_acc_soil_co.tif")
    acc_bio_name = os.path.join(intermediate_dir, "%i_acc_bio.tif")
    acc_bio_co_name = os.path.join(intermediate_dir, "%i_%i_acc_bio_co.tif")
    

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

    #totals
    total_acc_soil_name = "total_soil_acc_%i_%i.tif"
    total_acc_bio_name = "total_bio_acc_%i_%i.tif"
    total_dis_soil_name = "total_soil_dis_%i_%i.tif"
    total_dis_bio_name = "total_bio_dis_%i_%i.tif"
    net_sequestration_name = "net_sequest_%i_%i.tif"

    #uri
    total_acc_soil_uri = os.path.join(workspace_dir, total_acc_soil_name % (lulc_years[0], analysis_year))
    total_acc_bio_uri = os.path.join(workspace_dir, total_acc_bio_name % (lulc_years[0], analysis_year))
    total_dis_soil_uri = os.path.join(workspace_dir, total_dis_soil_name % (lulc_years[0], analysis_year))
    total_dis_bio_uri = os.path.join(workspace_dir, total_dis_bio_name % (lulc_years[0], analysis_year))

    extent_uri = os.path.join(workspace_dir, extent_name)
    report_uri = os.path.join(workspace_dir, report_name)
    
    ##process inputs
    #load tables from files
    acc_soil = raster_utils.get_lookup_from_csv(acc_soil_csv_uri, acc_soil_field_key)
    acc_bio = raster_utils.get_lookup_from_csv(acc_bio_csv_uri, acc_bio_field_key)

    dis_bio = raster_utils.get_lookup_from_csv(dis_bio_csv_uri, dis_field_key)
    dis_soil = raster_utils.get_lookup_from_csv(dis_soil_csv_uri, dis_field_key)

    trans = raster_utils.get_lookup_from_csv(trans_uri, trans_field_key)
    carbon = raster_utils.get_lookup_from_csv(carbon_uri, carbon_field_key)

    half_life = raster_utils.get_lookup_from_csv(half_life_csv_uri, half_life_field_key)

    #validate disturbance and accumulation tables
    change_types = set()
    for k1 in trans:
        for k2 in trans:
            change_types.add(trans[k1][str(k2)])

    change_columns = set(acc_soil[random.choice(list(acc_soil.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Soil accumulation table valid.")
    else:
        msg = "The transition matrix contains the following value(s) not in soil the accumulation table: %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(dis_soil[random.choice(list(dis_soil.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Soil disturbance table valid.")
    else:
        msg = "The transition matrix contains the following value(s) not in the soil disturbance table: %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(acc_bio[random.choice(list(acc_bio.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Biomass accumulation table valid.")
    else:
        msg = "The transition matrix contains the following value(s) not in the biomass accumulation table: %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(dis_bio[random.choice(list(dis_bio.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Biomass disturbance table valid.")
    else:
        msg = "The transition matrix contains the following value(s) not in the biomass disturbance table: %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    #construct dictionaries for single parameter lookups
    conversion = raster_utils.get_cell_size_from_uri(lulc_uri_dict[lulc_years[0]]) ** 2 / 10000.0 #convert to Ha

    above_dict = dict([(k, float(carbon[k][carbon_field_above]) * conversion) for k in carbon])
    below_dict = dict([(k, float(carbon[k][carbon_field_below]) * conversion) for k in carbon])
    litter_dict = dict([(k, float(carbon[k][carbon_field_litter]) * conversion) for k in carbon])
    depth_dict = dict([(k, float(carbon[k][carbon_field_depth]) * conversion) for k in carbon])
    soil_dict = dict([(k, float(carbon[k][carbon_field_soil]) * conversion * depth_dict[k]) for k in carbon])
    veg_dict = dict([(k, int(carbon[k][carbon_field_veg])) for k in carbon])
    
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
        if nodata_default_int in values:
            return nodata_default_int
        return reduce(operator.add,values)

    def mul_op(*values):
        if nodata_default_int in values:
            return nodata_default_int
        return reduce(operator.mul,values)

    #custom ops
    def acc_soil_co_op(lulc_base, lulc_transition):
        if nodata_lulc in [lulc_base, lulc_transition]:
            return nodata_default_float
        return float(acc_soil[carbon[int(lulc_base)][carbon_field_veg]]\
                     [trans[int(lulc_base)][str(int(lulc_transition))]])

    def acc_bio_co_op(lulc_base, lulc_transition):
        if nodata_lulc in [lulc_base, lulc_transition]:
            return nodata_default_float
        return float(acc_bio[carbon[int(lulc_base)][carbon_field_veg]]\
                     [trans[int(lulc_base)][str(int(lulc_transition))]])

    def dis_bio_co_op(lulc_base, lulc_transition):
        if nodata_lulc in [lulc_base, lulc_transition]:
            return nodata_default_float
        return float(dis_bio[carbon[int(lulc_base)][carbon_field_veg]]\
                     [trans[int(lulc_base)][str(int(lulc_transition))]])

    def dis_soil_co_op(lulc_base, lulc_transition):
        if nodata_lulc in [lulc_base, lulc_transition]:
            return nodata_default_float
        return float(dis_soil[carbon[int(lulc_base)][carbon_field_veg]]\
                     [trans[int(lulc_base)][str(int(lulc_transition))]])

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

    LOGGER.info("Running analysis.")
    ##calculate stock carbon values
    this_year = lulc_years[0]
    this_uri = lulc_uri_dict[this_year]

    #add reclass entry for nodata
    above_dict[int(nodata_lulc)] = nodata_default_float
    below_dict[int(nodata_lulc)] = nodata_default_float
    soil_dict[int(nodata_lulc)] = nodata_default_float
    litter_dict[int(nodata_lulc)] = nodata_default_float
    depth_dict[int(nodata_lulc)] = nodata_default_float

    LOGGER.info("Calculating stock carbon values.")
    #local variable names
    this_above_uri = os.path.join(workspace_dir, above_name % this_year)
    this_below_uri = os.path.join(workspace_dir, below_name % this_year)
    this_soil_uri = os.path.join(workspace_dir, soil_name % this_year)
    this_litter_uri = os.path.join(workspace_dir, litter_name % this_year)
    this_bio_uri = os.path.join(workspace_dir, bio_name % this_year)

    #create stock carbon values
    raster_utils.reclassify_dataset_uri(this_uri,
                               above_dict,
                               this_above_uri,
                               gdal_type_carbon,
                               nodata_default_float,
                               exception_flag="values_required")
    LOGGER.debug("Created stock above raster.")

    raster_utils.reclassify_dataset_uri(this_uri,
                               below_dict,
                               this_below_uri,
                               gdal_type_carbon,
                               nodata_default_float,
                               exception_flag="values_required")
    LOGGER.debug("Created stock below raster.")

    raster_utils.reclassify_dataset_uri(this_uri,
                               soil_dict,
                               this_soil_uri,
                               gdal_type_carbon,
                               nodata_default_float,
                               exception_flag="values_required")
    LOGGER.debug("Created stock soil raster.")

    raster_utils.vectorize_datasets([this_above_uri, this_below_uri],
                                    add_op,
                                    this_bio_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Created stock biomass raster.")

    this_adj_soil_uri = this_soil_uri
    this_adj_bio_uri = this_bio_uri
    
    this_dis_bio_half_uri = os.path.join(workspace_dir, dis_bio_half_name)
    this_dis_bio_em_uri = os.path.join(workspace_dir, dis_bio_em_name)
    this_dis_bio_adj_uri = os.path.join(workspace_dir, dis_bio_adj_name)

    this_dis_soil_half_uri = os.path.join(workspace_dir, dis_soil_half_name)
    this_dis_soil_em_uri = os.path.join(workspace_dir, dis_soil_em_name)
    this_dis_soil_adj_uri = os.path.join(workspace_dir, dis_soil_adj_name)

    ##loop over lulc years
    for next_year in lulc_years[1:] + [analysis_year]:
        
        t = next_year - this_year

        #local variable names
        this_litter_uri = os.path.join(workspace_dir, litter_name % this_year)
        this_adj_uri = os.path.join(workspace_dir, carbon_name % this_year)
        
        this_acc_soil_co_uri = os.path.join(workspace_dir, acc_soil_co_name % (this_year, next_year))
        this_acc_soil_uri = os.path.join(workspace_dir, acc_soil_name % this_year)

        this_acc_bio_co_uri = os.path.join(workspace_dir, acc_bio_co_name % (this_year, next_year))
        this_acc_bio_uri = os.path.join(workspace_dir, acc_bio_name % this_year)        

        this_dis_bio_co_uri = os.path.join(workspace_dir, dis_bio_co_name % (this_year, next_year))
        this_dis_bio_uri = os.path.join(workspace_dir, dis_bio_name % this_year)

        this_dis_soil_co_uri = os.path.join(workspace_dir, dis_soil_co_name % (this_year, next_year))
        this_dis_soil_uri = os.path.join(workspace_dir, dis_soil_name % this_year)

        LOGGER.debug("Base year %i.", this_year)

        raster_utils.reclassify_dataset_uri(this_uri,
                                   litter_dict,
                                   this_litter_uri,
                                   gdal_type_carbon,
                                   nodata_default_float,
                                   exception_flag="values_required")
        LOGGER.debug("Created stock litter raster.")

        raster_utils.vectorize_datasets([this_adj_bio_uri, this_adj_soil_uri, this_litter_uri],
                                        add_op,
                                        this_adj_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Created total carbon raster.")

        LOGGER.debug("Transition year %i.", next_year)
        next_uri = lulc_uri_dict[next_year]
        next_adj_soil_uri = os.path.join(workspace_dir, adj_soil_name % next_year)
        next_adj_bio_uri = os.path.join(workspace_dir, adj_bio_name % next_year)

        ##calculate soil accumulation
        LOGGER.info("Processing soil accumulation.")
        #get coefficients
        raster_utils.vectorize_datasets([this_uri, next_uri],
                                        acc_soil_co_op,
                                        this_acc_soil_co_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")

        LOGGER.debug("Accumulation coefficent raster created.")

        #multiply by number of years
        raster_utils.vectorize_datasets([this_acc_soil_co_uri],
                                        ConstantOp(mul_op,t),
                                        this_acc_soil_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Soil accumulation raster created.")

        ##calculate biomass accumulation
        LOGGER.info("Processing biomass accumulation.")
        #get coefficients
        raster_utils.vectorize_datasets([this_uri, next_uri],
                                        acc_bio_co_op,
                                        this_acc_bio_co_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Accumulation coefficent raster created.")

        #multiply by number of years
        raster_utils.vectorize_datasets([this_acc_bio_co_uri],
                                        ConstantOp(mul_op,t),
                                        this_acc_bio_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Biomass accumulation raster created.")

        ##calculate biomass disturbance
        LOGGER.info("Processing biomass disturbance.")
        #get coefficients
        raster_utils.vectorize_datasets([this_uri, next_uri],
                                        dis_bio_co_op,
                                        this_dis_bio_co_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")

        LOGGER.debug("Biomass disturbance coefficient raster created.")

        #multiply coefficients by base biomass carbon
        raster_utils.vectorize_datasets([this_dis_bio_co_uri, this_adj_bio_uri],
                                        mul_op,
                                        this_dis_bio_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Biomass disturbance raster created.")

        ##calculate soil disturbance
        LOGGER.info("Processing soil disturbance.")
        #get coefficients
        raster_utils.vectorize_datasets([this_uri, next_uri],
                                        dis_soil_co_op,
                                        this_dis_soil_co_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Soil disturbance coefficient raster created.")

        #multiply coefficients by base soil carbon
        raster_utils.vectorize_datasets([this_dis_soil_co_uri, this_adj_soil_uri],
                                        mul_op,
                                        this_dis_soil_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Soil disturbance raster created.")

        ##calculate adjusted carbon
        #calculate adjusted soil
        raster_utils.vectorize_datasets([this_adj_soil_uri,
                                         this_acc_soil_uri,
                                         this_dis_soil_uri],
                                         adj_op,
                                         next_adj_soil_uri,
                                         gdal_type_carbon,
                                         nodata_default_float,
                                         cell_size,
                                         "union")
        LOGGER.debug("Calculated adjusted soil carbon.")

        #calculate adjusted biomass
        raster_utils.vectorize_datasets([this_adj_bio_uri,
                                         this_acc_soil_uri,
                                         this_dis_soil_uri],
                                         adj_op,
                                         next_adj_bio_uri,
                                         gdal_type_carbon,
                                         nodata_default_float,
                                         cell_size,
                                        "union")
        LOGGER.debug("Calculated adjusted biomass carbon.")         

        ##change base year variables
        this_year = next_year
        this_uri = lulc_uri_dict[this_year]
        this_adj_soil_uri = next_adj_soil_uri
        this_adj_bio_uri = next_adj_bio_uri

    ##calculate emission
    veg_types = list(set([carbon[k][carbon_field_veg] for k in carbon]))
    veg_types.sort()

    emission_bio = {}
    emission_soil = {}
    dis_bio = dict(zip(veg_types, [0] * len(veg_types)))
    dis_soil = dict(zip(veg_types, [0] * len(veg_types)))
    for this_year in range(lulc_years[0], analysis_year +1):
        emission_bio[this_year]={}
        emission_soil[this_year]={}
        
        if this_year in lulc_years:
            #reclass LULC by vegetation type
            this_uri = lulc_uri_dict[this_year]
            this_veg_uri = os.path.join(workspace_dir, "%i_veg.tif" % this_year)

            raster_utils.reclassify_dataset_uri(this_uri,
                                       veg_dict,
                                       this_veg_uri,
                                       gdal_type_identity_raster,
                                       nodata_default_int,
                                       exception_flag="values_required")

            this_dis_bio_uri = os.path.join(workspace_dir, dis_bio_name % this_year)
            this_dis_soil_uri = os.path.join(workspace_dir, dis_soil_name % this_year)

            #tabulate disturbed carbon by vegetation type
            this_dis_bio = sum_by_category_uri(this_veg_uri, this_dis_bio_uri)
            for veg in this_dis_bio:
                dis_bio[veg] += this_dis_bio[veg]

            this_dis_soil = sum_by_category_uri(this_veg_uri, this_dis_soil_uri)
            for veg in this_dis_soil:
                dis_soil[veg] += this_dis_soil[veg]

        #apply half-life to generate 
        for veg in veg_types:
            try:
                alpha = float(half_life[veg][half_life_field_bio])
                emission_bio[this_year][veg]=dis_bio[veg] * (0.5 ** (1 / alpha))
            except ValueError:
                emission_bio[this_year][veg]=0
            dis_bio[veg]-=emission_bio[this_year][veg]

            try:
                alpha = float(half_life[veg][half_life_field_soil])
                emission_soil[this_year][veg]=dis_soil[veg] * (0.5 ** (1 / alpha))
            except ValueError:
                emission_soil[this_year][veg]=0
            dis_soil[veg]-=emission_soil[this_year][veg]

    ##analysis year calculations
    #copy litter for analysis year
    next_litter_uri = os.path.join(workspace_dir, litter_name % next_year)
    driver = gdal.GetDriverByName("GTIff")
    src_ds = gdal.Open(this_litter_uri)
    dst_ds = driver.CreateCopy(next_litter_uri, src_ds)
    dst_ds = None
    src_ds = None
    this_litter_uri = next_litter_uri
    this_adj_uri = os.path.join(workspace_dir, carbon_name % next_year)

    #calculate total carbon
    raster_utils.vectorize_datasets([this_adj_bio_uri, this_adj_soil_uri, this_litter_uri],
                                    add_op,
                                    this_adj_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Created total carbon raster.")  

    ##calculate totals
    LOGGER.info("Calculating totals.")

    acc_soil_uri_list = [os.path.join(workspace_dir, acc_soil_name % year) for year in lulc_years]
    acc_bio_uri_list = [os.path.join(workspace_dir, acc_bio_name % year) for year in lulc_years]
    dis_soil_uri_list = [os.path.join(workspace_dir, dis_soil_name % year) for year in lulc_years]
    dis_bio_uri_list = [os.path.join(workspace_dir, acc_soil_name % year) for year in lulc_years]

    raster_utils.vectorize_datasets(acc_soil_uri_list,
                                    add_op,
                                    total_acc_soil_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Cumilative soil accumulation raster created.")

    raster_utils.vectorize_datasets(acc_bio_uri_list,
                                    add_op,
                                    total_acc_bio_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Cumilative biomass accumulation raster created.")        

    raster_utils.vectorize_datasets(dis_soil_uri_list,
                                    add_op,
                                    total_dis_soil_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Cumilative soil disturbance raster created.")

    raster_utils.vectorize_datasets(dis_bio_uri_list,
                                    add_op,
                                    total_dis_bio_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Cumilative biomass disturbance raster created.")
    
    net_sequestration_uri = os.path.join(workspace_dir, net_sequestration_name % (lulc_years[0], analysis_year))                               
    raster_utils.vectorize_datasets([total_acc_bio_uri, total_dis_bio_uri, total_acc_soil_uri, total_dis_soil_uri],
                                    net_sequestration_op,
                                    net_sequestration_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Net sequestration raster created.")
    

    ##calculate totals in rasters and write report
    LOGGER.info("Tabulating data and generating report.")
    #create extent shapefile
    datasource_from_dataset_bounding_box_uri(total_acc_soil_uri, extent_uri)

    #open report
    report = open(report_uri, 'w')
    report.write("<HTML><TITLE>InVEST - Blue Carbon Report</TITLE><BODY>")

    #soil disturbance and accumulation table
    report.write("<B>Soil Disturbance and Accumulation</B>")
    column_name_list = ["Year", "Disturbance", "Accumulation", "Net", "Total"]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))
    d_total = 0
    a_total = 0    
    total = 0
    for year, d_uri, a_uri in zip(lulc_years, dis_soil_uri_list, acc_soil_uri_list):
        try:
            d = sum_uri(d_uri, extent_uri)
        except Exception:
            d = 0
        try:
            a = sum_uri(a_uri, extent_uri)
        except Exception:
            a = 0

        d_total += d
        a_total += a        

        net = a - d
        total += net

        report.write("\n<TR><TD>%s</TD></TR>" % "</TD><TD>".join(map(str,[year, d, a, net, total])))

    try:
        d = sum_uri(total_dis_soil_uri, extent_uri)
    except Exception:
        d = 0
    try:
        a = sum_uri(total_acc_soil_uri, extent_uri)
    except Exception:
        a = 0
    net = a - d        
    total = net
    report.write("\n<TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(map(str,["Total", d, a, net, total])))
    report.write("\n</TABLE>")

    #biomass disturbance table
    report.write("\n<P><P><B>Biomass Disturbance and Accumulation</B>")
    column_name_list = ["Year", "Disturbance", "Accumulation", "Net", "Total"]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))
    d_total = 0
    a_total = 0    
    total = 0
    for year, d_uri, a_uri in zip(lulc_years, dis_bio_uri_list, acc_bio_uri_list):
        try:
            d = sum_uri(d_uri, extent_uri)
        except Exception:
            d = 0
        try:
            a = sum_uri(a_uri, extent_uri)
        except Exception:
            a = 0

        d_total += d
        a_total += a        

        net = a - d
        total += net

        report.write("\n<TR><TD>%s</TD></TR>" % "</TD><TD>".join(map(str,[year, d, a, net, total])))

    try:
        d = sum_uri(total_dis_soil_uri, extent_uri)
    except Exception:
        d = 0
    try:
        a = sum_uri(total_acc_soil_uri, extent_uri)
    except Exception:
        a = 0
    net = a - d        
    total = net
    report.write("\n<TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(map(str,["Total", d, a, net, total])))
    report.write("\n</TABLE>")    

    #totals
    report.write("\n<P><P><B>Totals</B>")
    column_name_list = ["Year", "Amount"]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))

    for year in lulc_years:
        report.write("\n<TR><TD>%i</TD><TD>%s</TD></TR>" % (year, str(sum_uri(os.path.join(workspace_dir, carbon_name % year), extent_uri))))

    report.write("\n</TABLE>")

    print emission_bio

    #emission table
    report.write("\n<P><P><B>Emissions</B>")
    column_name_list = ["Year"] + [str(veg) + " Bio" for veg in veg_types] + [str(veg) + " Soil" for veg in veg_types]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))
    for this_year in range(lulc_years[0], analysis_year +1):
        report.write("\n<TR>")
        if this_year in lulc_years:
            report.write("<TD><B>%i</B></TD>" % this_year)
        else:
            report.write("<TD>%i</TD>" % this_year)
        for veg in veg_types:
            report.write("<TD>%s</TD>" % str(emission_bio[this_year][veg]))
        for veg in veg_types:
            report.write("<TD>%s</TD>" % str(emission_soil[this_year][veg]))
        report.write("</TR>")

    report.write("\n</TABLE>")        

    #lulc statistics
    report.write("\n<P><P><B>LULC Counts</B>")
    lulc_types = carbon.keys()
    lulc_types.sort()

    counts = {}
    count_max = 0
    for year in lulc_years:
        counts[year] = raster_utils.unique_raster_values_count(lulc_uri_dict[year])
        count_max = max([count_max] + [counts[year][k] for k in counts[year]])

    width = int(math.ceil(math.log10(count_max)))

    column_name_list = ["Year"] + [str(lulc).ljust(width, "#").replace("#", "&ensp;") for lulc in lulc_types]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))

    for year in lulc_years:
        report.write("<P><TR align=\"right\"><TD>%i</TD>" % year)
        for lulc in lulc_types:
            try:
                report.write("<TD>%i</TD>" % counts[year][lulc])
            except KeyError:
                report.write("<TD>%i</TD>" % 0)
        report.write("</TR>")

    report.write("\n</TABLE>")

    #close report
    report.close()

##
##    ##clean up
##    driver = gdal.GetDriverByName('GTiff')
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
