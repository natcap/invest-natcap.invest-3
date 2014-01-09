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
    above_name = os.path.join(intermediate_dir, "%i_base_above.tif")
    below_name = os.path.join(intermediate_dir, "%i_base_below.tif")
    soil_name = os.path.join(intermediate_dir, "%i_base_soil.tif")
    litter_name = os.path.join(intermediate_dir, "%i_base_litter.tif")
    biomass_name = os.path.join(intermediate_dir, "%i_base_biomass.tif")
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
    net_sequestration_name = "sequest_%i_%i.tif"

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

    #validate disturbance and accumulation tables
    change_types = set()
    for k1 in trans:
        for k2 in trans:
            change_types.add(trans[k1][str(k2)])

    change_columns = set(acc_soil[random.choice(list(acc_soil.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Soil accumulation table valid.")
    else:
        msg = "Soil accumulation table missing column(s): %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(dis_soil[random.choice(list(dis_soil.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Soil disturbance table valid.")
    else:
        msg = "Soil disturbance table missing column(s): %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(acc_bio[random.choice(list(acc_bio.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Biomass accumulation table valid.")
    else:
        msg = "Biomass accumulation table missing column(s): %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    change_columns = set(dis_bio[random.choice(list(dis_bio.keys()))].keys())
    if change_columns.issuperset(change_types):
        LOGGER.debug("Biomass disturbance table valid.")
    else:
        msg = "Biomass disturbance table missing column(s): %s", str(change_types.difference(change_columns))
        LOGGER.error(msg)
        raise ValueError, msg

    #construct dictionaries for single parameter lookups
    above_dict = dict([(k, float(carbon[k][carbon_field_above])) for k in carbon])
    below_dict = dict([(k, float(carbon[k][carbon_field_below])) for k in carbon])
    soil_dict = dict([(k, float(carbon[k][carbon_field_soil])) for k in carbon])
    litter_dict = dict([(k, float(carbon[k][carbon_field_litter])) for k in carbon])
    depth_dict = dict([(k, float(carbon[k][carbon_field_depth])) for k in carbon])

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

    LOGGER.info("Running analysis.")
    ##calculate stock carbon values
    lulc_base_year = lulc_years[0]
    lulc_base_uri = lulc_uri_dict[lulc_base_year]

    #add reclass entry for nodata
    above_dict[int(nodata_lulc)] = nodata_default_float
    below_dict[int(nodata_lulc)] = nodata_default_float
    soil_dict[int(nodata_lulc)] = nodata_default_float
    litter_dict[int(nodata_lulc)] = nodata_default_float
    depth_dict[int(nodata_lulc)] = nodata_default_float

    ##loop over lulc years
    for lulc_transition_year in lulc_years[1:] + [analysis_year]:
        
        t = lulc_transition_year - lulc_base_year

        #local variable names
        lulc_base_above_uri = os.path.join(workspace_dir, above_name % lulc_base_year)
        lulc_base_below_uri = os.path.join(workspace_dir, below_name % lulc_base_year)
        lulc_base_soil_uri = os.path.join(workspace_dir, soil_name % lulc_base_year)
        lulc_base_litter_uri = os.path.join(workspace_dir, litter_name % lulc_base_year)
        lulc_base_biomass_uri = os.path.join(workspace_dir, biomass_name % lulc_base_year)
        lulc_base_carbon_uri = os.path.join(workspace_dir, carbon_name % lulc_base_year)
        
        lulc_base_acc_soil_co_uri = os.path.join(workspace_dir, acc_soil_co_name % (lulc_base_year, lulc_transition_year))
        lulc_base_acc_soil_uri = os.path.join(workspace_dir, acc_soil_name % lulc_base_year)

        lulc_base_acc_bio_co_uri = os.path.join(workspace_dir, acc_bio_co_name % (lulc_base_year, lulc_transition_year))
        lulc_base_acc_bio_uri = os.path.join(workspace_dir, acc_bio_name % lulc_base_year)        

        lulc_base_dis_bio_co_uri = os.path.join(workspace_dir, dis_bio_co_name % (lulc_base_year, lulc_transition_year))
        lulc_base_dis_bio_uri = os.path.join(workspace_dir, dis_bio_name % lulc_base_year)

        lulc_base_dis_soil_co_uri = os.path.join(workspace_dir, dis_soil_co_name % (lulc_base_year, lulc_transition_year))
        lulc_base_dis_soil_uri = os.path.join(workspace_dir, dis_soil_name % lulc_base_year)


        LOGGER.info("Calculating stock carbon values.")
        #create stock carbon values
        raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                   above_dict,
                                   lulc_base_above_uri,
                                   gdal_type_carbon,
                                   nodata_default_float,
                                   exception_flag="values_required")
        LOGGER.debug("Created stock above raster: %s", os.path.basename(lulc_base_above_uri))

        raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                   below_dict,
                                   lulc_base_below_uri,
                                   gdal_type_carbon,
                                   nodata_default_float,
                                   exception_flag="values_required")
        LOGGER.debug("Created stock below raster.")

        raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                   soil_dict,
                                   lulc_base_soil_uri,
                                   gdal_type_carbon,
                                   nodata_default_float,
                                   exception_flag="values_required")
        LOGGER.debug("Created stock soil raster.")

        raster_utils.reclassify_dataset_uri(lulc_base_uri,
                                   litter_dict,
                                   lulc_base_litter_uri,
                                   gdal_type_carbon,
                                   nodata_default_float,
                                   exception_flag="values_required")
        LOGGER.debug("Created stock litter raster.")

        raster_utils.vectorize_datasets([lulc_base_above_uri, lulc_base_below_uri],
                                        add_op,
                                        lulc_base_biomass_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Created stock biomass raster.")

        raster_utils.vectorize_datasets([lulc_base_biomass_uri, lulc_base_soil_uri],
                                        add_op,
                                        lulc_base_carbon_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Created stock total raster.")

        if not (lulc_transition_year == analysis_year):
            LOGGER.debug("Transition year %i.", lulc_transition_year)
            lulc_transition_uri = lulc_uri_dict[lulc_transition_year]

            ##calculate soil accumulation
            LOGGER.info("Processing soil accumulation.")
            #get coefficients
            try:
                raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                                acc_soil_co_op,
                                                lulc_base_acc_soil_co_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")

                LOGGER.debug("Accumulation coefficent raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_acc_soil_co_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Identity raster for soil accumulation coefficent created.")

            #multiply by number of years
            try:
                raster_utils.vectorize_datasets([lulc_base_acc_soil_co_uri],
                                                ConstantOp(mul_op,t),
                                                lulc_base_acc_soil_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")
                LOGGER.debug("Soil accumulation raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_acc_soil_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Zero soil accumulation raster created.")

            ##calculate biomass accumulation
            LOGGER.info("Processing biomass accumulation.")
            #get coefficients
            try:
                raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                                acc_bio_co_op,
                                                lulc_base_acc_bio_co_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")

                LOGGER.debug("Accumulation coefficent raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_acc_bio_co_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Identity raster for biomass accumulation coefficent created.")

            #multiply by number of years
            try:
                raster_utils.vectorize_datasets([lulc_base_acc_bio_co_uri],
                                                ConstantOp(mul_op,t),
                                                lulc_base_acc_bio_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")
                LOGGER.debug("Biomass accumulation raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_acc_bio_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Zero biomass accumulation raster created.")

            ##calculate biomass disturbance
            LOGGER.info("Processing biomass disturbance.")
            #get coefficients
            try:
                raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                                biomass_disturbance_co_op,
                                                lulc_base_dis_bio_co_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")

                LOGGER.debug("Biomass disturbance coeffiicent raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_dis_bio_co_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Identity raster for biomass disturbance coefficent created.")

            #multiply coefficients by base biomass carbon
            try:
                raster_utils.vectorize_datasets([lulc_base_dis_bio_co_uri, lulc_base_biomass_uri],
                                                mul_op,
                                                lulc_base_dis_bio_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")
                LOGGER.debug("Biomass disturbance raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_dis_bio_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Zero biomass disturbance raster created.")

            ##calculate soil disturbance
            LOGGER.info("Processing soil disturbance.")
            #get coefficients
            try:
                raster_utils.vectorize_datasets([lulc_base_uri, lulc_transition_uri],
                                                soil_disturbance_co_op,
                                                lulc_base_dis_soil_co_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")
                LOGGER.debug("Soil disturbance coefficient raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_dis_soil_co_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Identity raster for soil disturbance created.")


            #multiply coefficients by base soil carbon
            try:
                raster_utils.vectorize_datasets([lulc_base_dis_soil_co_uri, lulc_base_soil_uri],
                                                mul_op,
                                                lulc_base_dis_soil_uri,
                                                gdal_type_carbon,
                                                nodata_default_float,
                                                cell_size,
                                                "union")
                LOGGER.debug("Soil disturbance raster created.")

            except:
                raster_utils.new_raster_from_base_uri(lulc_base_uri,
                                                      lulc_base_dis_soil_uri,
                                                      gdal_format,
                                                      nodata_default_int,
                                                      gdal_type_identity_raster,
                                                      fill_value=0)
                LOGGER.debug("Zero soil disturbance raster created.")

            #set base to new LULC and year
            lulc_base_year = lulc_transition_year
            LOGGER.debug("Changed base year to %i." % lulc_base_year)

            lulc_base_uri = lulc_uri_dict[lulc_base_year]
            LOGGER.debug("Changed base uri to. %s" % lulc_base_uri)    

    ##calculate adjusted pools
    LOGGER.debug(str(lulc_years))
    LOGGER.info("Calculating adjusted pools.")
    def adj_op(base, acc, dis):
        if nodata_default_float in [base, acc, dis]:
            return nodata_default_float
        else:
            return base + acc - dis

    base_year = lulc_years[0]
    transition_year = lulc_years[1]
    adj_bio_uri = os.path.join(workspace_dir,adj_bio_name % transition_year)
    adj_soil_uri = os.path.join(workspace_dir, adj_soil_name % transition_year)
    raster_utils.vectorize_datasets([os.path.join(workspace_dir, above_name % base_year),
                                     os.path.join(workspace_dir,acc_soil_name % base_year),
                                     os.path.join(workspace_dir,dis_soil_name % base_year)],
                                    adj_op,
                                    adj_soil_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Calculated adjusted soil carbon: %s", os.path.basename(adj_soil_uri))

    #calculate adjusted biomass
    raster_utils.vectorize_datasets([os.path.join(workspace_dir,biomass_name % base_year),
                                     os.path.join(workspace_dir,acc_bio_name % base_year),
                                     os.path.join(workspace_dir,dis_bio_name % base_year)],
                                    adj_op,
                                    adj_bio_uri,
                                    gdal_type_carbon,
                                    nodata_default_float,
                                    cell_size,
                                    "union")
    LOGGER.debug("Calculated adjusted biomass carbon: %s", os.path.basename(adj_bio_uri))                                        


    base_year = transition_year
    for transition_year in lulc_years[2:]:
        adj_bio_uri = os.path.join(workspace_dir,adj_bio_name % transition_year)
        adj_soil_uri = os.path.join(workspace_dir,adj_soil_name % transition_year)

        #calculate adjusted soil
        raster_utils.vectorize_datasets([os.path.join(workspace_dir,adj_soil_name % base_year),
                                         os.path.join(workspace_dir,acc_soil_name % base_year),
                                         os.path.join(workspace_dir,dis_soil_name % base_year)],
                                        adj_op,
                                        adj_soil_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Calculated adjusted soil carbon: %s", os.path.basename(adj_soil_uri))                                        

        #calculate adjusted biomass
        raster_utils.vectorize_datasets([os.path.join(workspace_dir,adj_bio_name % base_year),
                                         os.path.join(workspace_dir,acc_bio_name % base_year),
                                         os.path.join(workspace_dir,dis_bio_name % base_year)],
                                        adj_op,
                                        adj_bio_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
        LOGGER.debug("Calculated adjusted biomass carbon: %s", os.path.basename(adj_bio_uri))                                        

        
        base_year = transition_year


    ##calculate totals
    LOGGER.info("Calculating totals.")
    #construct list of rasters for totals
    lulc_years = lulc_uri_dict.keys()
    lulc_years.sort()

    acc_soil_uri_list = []
    acc_bio_uri_list = []
    dis_soil_uri_list = []
    dis_bio_uri_list = []

    for year in lulc_years[:-1]:
        acc_soil_uri_list.append(os.path.join(workspace_dir, acc_soil_name % year))
        acc_bio_uri_list.append(os.path.join(workspace_dir, acc_bio_name % year))
        dis_soil_uri_list.append(os.path.join(workspace_dir, dis_soil_name % year))
        dis_bio_uri_list.append(os.path.join(workspace_dir, dis_bio_name % year))

    try:
        raster_utils.vectorize_datasets(acc_soil_uri_list,
                                        add_op,
                                        total_acc_soil_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")

    except:
        raster_utils.new_raster_from_base_uri(acc_soil_uri_list[0],
                                              total_acc_soil_uri,
                                              gdal_format,
                                              nodata_default_int,
                                              gdal_type_identity_raster,
                                              fill_value=0)
    LOGGER.debug("Cumilative soil accumulation raster created.")

    try:
        raster_utils.vectorize_datasets(acc_bio_uri_list,
                                        add_op,
                                        total_acc_bio_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")

    except:
        raster_utils.new_raster_from_base_uri(acc_bio_uri_list[0],
                                              total_acc_bio_uri,
                                              gdal_format,
                                              nodata_default_int,
                                              gdal_type_identity_raster,
                                              fill_value=0)
    LOGGER.debug("Cumilative biomass accumulation raster created.")        

    try:                                              
        raster_utils.vectorize_datasets(dis_soil_uri_list,
                                        add_op,
                                        total_dis_soil_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
    except:
        raster_utils.new_raster_from_base_uri(dis_soil_uri_list[0],
                                      total_dis_soil_uri,
                                      gdal_format,
                                      nodata_default_int,
                                      gdal_type_identity_raster,
                                      fill_value=0)
    LOGGER.debug("Cumilative soil disturbance raster created.")

    try:                                              
        raster_utils.vectorize_datasets(dis_bio_uri_list,
                                        add_op,
                                        total_dis_bio_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
    except:
        raster_utils.new_raster_from_base_uri(dis_bio_uri_list[0],
                                      total_dis_bio_uri,
                                      gdal_format,
                                      nodata_default_int,
                                      gdal_type_identity_raster,
                                      fill_value=0)
    LOGGER.debug("Cumilative biomass disturbance raster created.")

    def net_sequestration_op(bio_acc, bio_dis, soil_acc, soil_dis):
        if nodata_default_float in [bio_acc, bio_dis, soil_acc, soil_dis]:
            return nodata_default_float
        else:
            return ((bio_acc + soil_acc) - (bio_dis + soil_dis))

    net_sequestration_uri = os.path.join(workspace_dir, net_sequestration_name % (lulc_years[0], lulc_years[-1]))
    try:                                              
        raster_utils.vectorize_datasets([total_acc_bio_uri, total_dis_bio_uri, total_acc_soil_uri, total_dis_soil_uri],
                                        net_sequestration_op,
                                        net_sequestration_uri,
                                        gdal_type_carbon,
                                        nodata_default_float,
                                        cell_size,
                                        "union")
    except:
        raster_utils.new_raster_from_base_uri(total_acc_bio_uri,
                                              net_sequestration_uri,
                                              gdal_format,
                                              nodata_default_int,
                                              gdal_type_identity_raster,
                                              fill_value=0)
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
    report.write("\n<P><P><B>Biomass Disturbance</B>")
    column_name_list = ["Year", "Amount", "Total"]
    report.write("\n<TABLE BORDER=1><TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(column_name_list))

    total = 0
    for year, d_uri in zip(lulc_years, dis_bio_uri_list):
        try:
            d = sum_uri(d_uri, extent_uri)
        except Exception:
            d = 0

        total += d

        report.write("\n<TR><TD>%s</TD></TR>" % "</TD><TD>".join(map(str,[year, d, total])))

    try:
        d = sum_uri(total_dis_bio_uri, extent_uri)
    except Exception:
        d = 0
        
    report.write("\n<TR><TD><B>%s</B></TD></TR>" % "</B></TD><TD><B>".join(map(str,["Total", d, d])))

    #close report
    report.close()


##    ##clean up
    driver = gdal.GetDriverByName('GTiff')
    for year in lulc_years[1:]:
        LOGGER.debug("Cleaning up intermediates for year %i." % year)
        driver.Delete(os.path.join(workspace_dir, above_name % year))
        driver.Delete(os.path.join(workspace_dir, below_name % year))
        driver.Delete(os.path.join(workspace_dir, soil_name % year))
        #driver.Delete(os.path.join(workspace_dir, litter_name % year))
        driver.Delete(os.path.join(workspace_dir, biomass_name % year))
        #driver.Delete(os.path.join(workspace_dir, carbon_name % year))

    for uri in acc_soil_uri_list+dis_soil_uri_list+dis_bio_uri_list:
        driver.Delete(uri)

    datasource = ogr.Open(extent_uri, 1)
    datasource.DeleteLayer(0)
    datasource = None
