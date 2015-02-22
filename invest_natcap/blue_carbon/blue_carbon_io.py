"""
(About Blue Carbon IO)
"""

import logging
import os
import operator
import pprint as pp

from osgeo import gdal, ogr, osr

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon')


def fetch_args(args):
    '''
    Fetches inputs for blue carbon model and returns dictionary of variables

    Example Args::

        args = {
            'workspace_dir': '/path/to/workspace_dir/',
            'lulc_uri_1': '/path/to/lulc_uri_1',
            'year_1': 2004,
            'lulc_uri_2': '/path/to/lulc_uri_2',
            'year_2': 2050,
            'lulc_uri_3': '/path/to/lulc_uri_3',
            'year_3': 2100,
            'lulc_uri_4': '/path/to/lulc_uri_4',
            'analysis_year': 2150,
            'soil_disturbance_csv_uri': '/path/to/csv',
            'biomass_disturbance_csv_uri': '/path/to/csv',
            'carbon_pools_uri': '/path/to/csv',
            'half_life_csv_uri': '/path/to/csv',
            'transition_matrix_uri': '/path/to/csv',
            'private_valuation': True,
            'discount_rate': 5,
            'price_table': True,
            'carbon_schedule': '/path/to/csv',
            'carbon_value': 43.00,
            'rate_change': 0,
        }

    Example Returns::

        vars = {
            # ... original args ...

            # Derived Variables

            # Raster Information
            'lulc_uri_dict': {
                '(lulc_year)': '(raster_uri)',
                ...
            },
            'lulc_years': [2004, 2050, 2100]
            'gdal_type_carbon': gdal.GDT_Float64,
            'cell_size': 1000,
            'nodata_default_int': -1,
            'nodata_default_float': -1,
            'nodata_lulc': 0,

            # Carbon Pools (Not Used - see veg_field_dict, trans_veg_acc_dict, trans_dis_dict)
            'carbon_pools': {
                '(Id)': {
                    'Above (Mg / ha)': 0,
                    'Below (Mg / ha)': 0,
                    ...
                },
                ...
            },
            'carbon_field_soil': 'Soil (Mg / ha)',
            'carbon_field_litter': 'Litter (Mg / ha)',

            # Carbon Decay Rate for Vegetation/Disturbance Type
            'half_life': {
                '(id)': {
                    'biomass (years)': (float),
                    'soil (years)': (float),
                    'veg name': (string),
                    'veg type': (int)
                }
            },
            'half_life_field_key': 'veg_type',
            'half_life_field_bio': 'biomass (years)',
            'half_life_field_soil': 'soil (years)',

            'veg_field_dict': {
                (veg_type): {
                    'Above (Mg / ha)': {
                        (Id): (???), ...
                    }, ...
                }, ...
            },
            'veg_type_list': [0, 1, 2],

            # (EXPLAIN)
            'trans_veg_acc_dict': {
                '(veg_type)': {
                    'acc_soil': {
                        (original_lulc, transition_lulc): (accumulation),
                        ...
                    },
                    'acc_bio': {
                        (original_lulc, transition_lulc): (accumulation),
                        ...
                    },
                }, ...
            },

            # Transition Matrix for Carbon Flow
            'trans_dis_dict': {
                'dis_bio': {  # <-- derived from biomass_disturbance_csv_uri
                    (original_lulc, transition_lulc): (disturbance),
                    ...
                },
                'dis_soil': {  # <-- derived from soil_disturbance_csv_uri
                    (original_lulc, transition_lulc): (disturbance),
                    ...
                }
            },
            'dis_soil_key': 'dis_soil',
            'dis_bio_key': 'dis_bio',
            'acc_soil_key': 'acc_soil',
            'acc_bio_key': 'acc_bio',

            # Intermediate Outputs
            'intermediate_dir': '/path/to/intermediate/',
            'veg_stock_bio_uris': '/path/to/%i_veg_%i_stock_biomass.tif',
            'veg_stock_soil_uris': '/path/to/%i_veg_%i_stock_soil.tif',
            'veg_litter_uris': '/path/to/%i_veg_%i_litter.tif',
            'acc_soil_uris': '/path/to/%i_acc_soil.tif',
            'acc_bio_uris': '/path/to/%i_acc_bio.tif',
            'veg_acc_bio_uris': '/path/to/%i_%i_veg_%i_acc_bio.tif',
            'veg_acc_soil_uris': '/path/to/%i_%i_veg_%i_acc_soil.tif',
            'veg_dis_bio_uris': '/path/to/%i_%i_veg_%i_dis_bio.tif',
            'veg_dis_soil_uris': '/path/to/%i_%i_veg_%i_dis_soil.tif',
            'dis_bio_uris': '/path/to/%i_dis_bio.tif',
            'dis_soil_uris': '/path/to/%i_dis_soil.tif',
            'veg_adj_acc_bio_uris': '/path/to/%i_%i_veg_%i_adj_acc_bio.tif',
            'veg_adj_acc_soil_uris': '/path/to/%i_%i_veg_%i_adj_acc_soil.tif',
            'veg_adj_dis_bio_uris': '/path/to/%i_%i_veg_%i_adj_dis_bio.tif',
            'veg_adj_dis_soil_uris': '/path/to/%i_%i_veg_%i_adj_dis_soil.tif',
            'veg_adj_em_dis_bio_uris': '/path/to/%i_%i_veg_%i_adj_em_dis_bio.tif',
            'veg_adj_em_dis_soil_uris': '/path/to/%i_%i_veg_%i_adj_em_dis_soil.tif',
            'veg_em_bio_uris': '/path/to/%i_%i_veg_%i_em_bio.tif',
            'veg_em_soil_uris': '/path/to/%i_%i_veg_%i_em_soil.tif',

            'this_total_acc_soil_uris': '/path/to/%i_%i_soil_acc.tif',
            'this_total_acc_bio_uris': '/path/to/%i_%i_bio_acc.tif',
            'this_total_dis_soil_uris': '/path/to/%i_%i_soil_dis.tif',
            'this_total_dis_bio_uris': '/path/to/%i_%i_bio_dis.tif',

            # Final Outputs
            'extent_uri': '/path/to/extent.shp',  # Bounding area of all input LULC maps
            'carbon_stock_uri': '/path/to/stock_%%i.tif',  # Carbon stock at time t
            'net_sequestration_uri': '/path/to/sequest_%i_%i.tif',  # Carbon sequested over given timeperiod
            'gain_uri': '/path/to/gain_%i_%i.tif',  # Only positive net sequestration
            'loss_uri': '/path/to/loss_%i_%i.tif',  # Only negative net sequestration
            'blue_carbon_csv_uri': '/path/to/sequestration.csv',  # Valuation table
        }

    '''
    vars_dict = dict(args.items())

    # === Create Workspace
    workspace_dir = args['workspace_dir']
    intermediate_dir = os.path.join(args['workspace_dir'], "intermediate")
    vars_dict['intermediate_dir'] = intermediate_dir

    if not os.path.exists(intermediate_dir):
        os.makedirs(intermediate_dir)

    # === Initialize Dictionaries from Input Tables

    # == Distrubance CSVs
    trans_acc = "Accumulation"
    dis_field_key = "veg type"

    # soil_disturbance_csv_uri - dis_soil
    vars_dict['dis_soil'] = raster_utils.get_lookup_from_csv(
        args["soil_disturbance_csv_uri"], dis_field_key)
    for k in vars_dict['dis_soil']:
        vars_dict['dis_soil'][k][trans_acc] = 0.0

    # biomass_disturbance_csv_uri - dis_bio
    vars_dict['dis_bio'] = raster_utils.get_lookup_from_csv(
        args["biomass_disturbance_csv_uri"], dis_field_key)
    for k in vars_dict['dis_bio']:
        vars_dict['dis_bio'][k][trans_acc] = 0.0

    # == Carbon Pools CSV
    carbon_field_veg = "Veg Type"
    carbon_field_above = "Above (Mg / ha)"
    carbon_field_below = "Below (Mg / ha)"
    carbon_acc_soil_field = "Soil_accum_rate (Mg / ha / yr)"
    carbon_acc_bio_field = "Bio_accum_rate (Mg / ha / yr)"
    vars_dict['carbon_field_litter'] = "Litter (Mg / ha)"
    carbon_field_soil = "Soil (Mg / ha)"
    vars_dict['carbon_field_soil'] = carbon_field_soil

    vars_dict['carbon_pools'] = raster_utils.get_lookup_from_csv(
        vars_dict['carbon_pools_uri'], "Id")

    # == Half Life CSV
    half_life_field_key = "veg type"
    vars_dict['half_life_field_bio'] = "biomass (years)"
    vars_dict['half_life_field_soil'] = "soil (years)"
    vars_dict['half_life'] = raster_utils.get_lookup_from_csv(
        vars_dict['half_life_csv_uri'],
        half_life_field_key)

    # == Transition Matrix CSV
    trans_csv_dict = raster_utils.get_lookup_from_csv(
        vars_dict['transition_matrix_uri'], "Id")

    ####################################
    #  NEW FUNCTION SHOULD GO HERE
    # === Initialize Derivative Dictionaries
    lulc_list = []
    for i in range(1, 6):
        if "year_%i" % i in args:
            lulc_list.append(
                {"uri": args["lulc_uri_%i" % i], "year": args["year_%i" % i]})
        else:
            break
    lulc_uri_dict = dict([(lulc["year"], lulc["uri"]) for lulc in lulc_list])
    lulc_years = lulc_uri_dict.keys()
    lulc_years.sort()
    # copy LULC for analysis year
    lulc_uri_dict[args["analysis_year"]] = lulc_uri_dict[lulc_years[-1]]
    vars_dict['lulc_uri_dict'] = lulc_uri_dict
    vars_dict['lulc_years'] = lulc_years

    _validate_rasters(vars_dict, trans_csv_dict, lulc_uri_dict, lulc_years)

    class InfiniteDict:
        def __init__(self, k, v):
            self.d = {k: v}

        def __getitem__(self, k):
            try:
                return self.d[k]
            except KeyError:
                return 0.0

        def __repr__(self):
            return repr(self.d)

    # constructing accumulation tables from carbon table
    # acc_soil - from carbon
    acc_soil = {}
    for k in vars_dict['carbon_pools']:
        acc_soil[k] = InfiniteDict(
            trans_acc,
            vars_dict['carbon_pools'][k][carbon_acc_soil_field])
    vars_dict['acc_soil'] = acc_soil

    # acc_bio - from carbon
    acc_bio = {}
    for k in vars_dict['carbon_pools']:
        acc_bio[k] = InfiniteDict(
            trans_acc,
            vars_dict['carbon_pools'][k][carbon_acc_bio_field])
    vars_dict['acc_bio'] = acc_bio

    # construct dictionaries for single parameter lookups
    conversion = (raster_utils.get_cell_size_from_uri(
        lulc_uri_dict[lulc_years[0]]) ** 2) / 10000.0  # convert to Ha

    LOGGER.debug("Cell size is %s hectacres.", conversion)

    veg_dict = dict([(k, int(vars_dict['carbon_pools'][k][
        carbon_field_veg])) for k in vars_dict['carbon_pools']])

    veg_type_list = list(set([veg_dict[k] for k in veg_dict]))
    vars_dict['veg_type_list'] = veg_type_list

    # create carbon field dictionary
    veg_field_dict = {}
    for veg_type in veg_type_list:
        veg_field_dict[veg_type] = {}
        for field in [carbon_field_above,
                      carbon_field_below,
                      vars_dict['carbon_field_litter'],
                      carbon_field_soil]:
            veg_field_dict[veg_type][field] = {}
            for k in vars_dict['carbon_pools']:
                if int(vars_dict['carbon_pools'][k][carbon_field_veg]) == veg_type:
                    veg_field_dict[veg_type][field][k] = float(
                        vars_dict['carbon_pools'][k][field]) * conversion
                else:
                    veg_field_dict[veg_type][field][k] = 0.0

    # add biomass to carbon field
    carbon_field_bio = "bio"
    for veg_type in veg_type_list:
        veg_field_dict[veg_type][carbon_field_bio] = {}
        for k in vars_dict['carbon_pools']:
            # sum (below, above) carbon pools together
            veg_field_dict[veg_type][carbon_field_bio][k] = veg_field_dict[
                veg_type][carbon_field_below][k] + veg_field_dict[veg_type][
                carbon_field_above][k]
    vars_dict['veg_field_dict'] = veg_field_dict
    vars_dict['carbon_field_bio'] = carbon_field_bio

    # accumulation
    trans_veg_acc_dict = {}
    for veg_type in veg_type_list:
        trans_veg_acc_dict[veg_type] = {}
        for component, component_dict in [
                ("acc_soil", acc_soil),
                ("acc_bio", acc_bio)]:
            trans_veg_acc_dict[veg_type][component] = {}
            for original_lulc in trans_csv_dict:
                trans_veg_acc_dict[veg_type][component][original_lulc] = {}
                for transition_lulc in trans_csv_dict:
                    if int(vars_dict['carbon_pools'][transition_lulc][
                            carbon_field_veg]) == veg_type:
                        trans_veg_acc_dict[veg_type][component][
                            (original_lulc, transition_lulc)] = component_dict[
                                transition_lulc][trans_csv_dict[
                                    original_lulc][str(
                                        transition_lulc)]] * conversion
                    else:
                        trans_veg_acc_dict[veg_type][component][(
                            original_lulc, transition_lulc)] = 0.0
    vars_dict['trans_veg_acc_dict'] = trans_veg_acc_dict

    # disturbance
    trans_dis_dict = {}
    for component, component_dict in [
            ("dis_bio", vars_dict['dis_bio']),
            ("dis_soil", vars_dict['dis_soil'])]:
        trans_dis_dict[component] = {}
        for original_lulc in trans_csv_dict:
            for transition_lulc in trans_csv_dict:
                trans_dis_dict[component][(original_lulc, transition_lulc)] = \
                    component_dict[vars_dict['carbon_pools'][original_lulc][
                        carbon_field_veg]][trans_csv_dict[original_lulc][
                            str(transition_lulc)]]
    vars_dict['trans_dis_dict'] = trans_dis_dict

    # === Constants
    vars_dict['gdal_type_carbon'] = gdal.GDT_Float64
    vars_dict['nodata_default_int'] = -1
    vars_dict['nodata_default_float'] = -1

    vars_dict['acc_soil_key'] = "acc_soil"
    vars_dict['acc_bio_key'] = "acc_bio"
    vars_dict['dis_bio_key'] = "dis_bio"
    vars_dict['dis_soil_key'] = "dis_soil"

    # === Create Output Raster URI Templates
    # carbon pool file names
    vars_dict['veg_stock_bio_uris'] = os.path.join(
        intermediate_dir, "%i_veg_%i_stock_biomass.tif")
    vars_dict['veg_stock_soil_uris'] = os.path.join(
        intermediate_dir, "%i_veg_%i_stock_soil.tif")

    # carbon litter
    vars_dict['veg_litter_uris'] = os.path.join(
        intermediate_dir, "%i_veg_%i_litter.tif")

    # carbon accumulation file names
    vars_dict['acc_soil_uris'] = os.path.join(
        intermediate_dir, "%i_acc_soil.tif")
    vars_dict['acc_bio_uris'] = os.path.join(
        intermediate_dir, "%i_acc_bio.tif")

    vars_dict['veg_acc_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_acc_bio.tif")
    vars_dict['veg_acc_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_acc_soil.tif")
    vars_dict['veg_dis_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_dis_bio.tif")
    vars_dict['veg_dis_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_dis_soil.tif")

    # carbon disturbance file names
    vars_dict['dis_bio_uris'] = os.path.join(
        intermediate_dir, "%i_dis_bio.tif")
    vars_dict['dis_soil_uris'] = os.path.join(
        intermediate_dir, "%i_dis_soil.tif")

    # adjusted carbon file names
    vars_dict['veg_adj_acc_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_acc_bio.tif")
    vars_dict['veg_adj_acc_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_acc_soil.tif")
    vars_dict['veg_adj_dis_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_dis_bio.tif")
    vars_dict['veg_adj_dis_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_dis_soil.tif")

    vars_dict['veg_adj_em_dis_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_em_dis_bio.tif")
    vars_dict['veg_adj_em_dis_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_adj_em_dis_soil.tif")

    # emission file names
    vars_dict['veg_em_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_em_bio.tif")
    vars_dict['veg_em_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_veg_%i_em_soil.tif")

    # totals
    vars_dict['this_total_acc_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_soil_acc.tif")
    vars_dict['this_total_acc_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_bio_acc.tif")
    vars_dict['this_total_dis_soil_uris'] = os.path.join(
        intermediate_dir, "%i_%i_soil_dis.tif")
    vars_dict['this_total_dis_bio_uris'] = os.path.join(
        intermediate_dir, "%i_%i_bio_dis.tif")

    # Create Output URIs
    vars_dict['extent_uri'] = os.path.join(
        workspace_dir, "extent.shp")
    vars_dict['blue_carbon_csv_uri'] = os.path.join(
        workspace_dir, "sequestration.csv")
    vars_dict['net_sequestration_uri'] = os.path.join(
        workspace_dir, "sequest_%i_%i.tif")
    vars_dict['gain_uri'] = os.path.join(
        workspace_dir, "gain_%i_%i.tif")
    vars_dict['loss_uri'] = os.path.join(
        workspace_dir, "loss_%i_%i.tif")
    vars_dict['carbon_stock_uri'] = os.path.join(
        workspace_dir, "stock_%i.tif")

    return vars_dict


def _alignment_check_uri(dataset_uri_list):
    '''

    '''
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


def _validate_rasters(vars_dict, trans_csv_dict, lulc_uri_dict, lulc_years):
    '''
    '''
    # validate disturbance and accumulation tables
    change_types = set()
    for k1 in trans_csv_dict:
        for k2 in trans_csv_dict:
            change_types.add(trans_csv_dict[k1][str(k2)])

    # check that all rasters have same nodata value
    vars_dict['nodata_lulc'] = set([raster_utils.get_nodata_from_uri(
        lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(vars_dict['nodata_lulc']) == 1:
        LOGGER.debug("All rasters have the same nodata value.")
        vars_dict['nodata_lulc'] = vars_dict['nodata_lulc'].pop()
    else:
        msg = "All rasters must have the same nodata value."
        LOGGER.error(msg)
        raise ValueError, msg

    # check that all rasters have same cell size
    vars_dict['cell_size'] = set([raster_utils.get_cell_size_from_uri(
        lulc_uri_dict[k]) for k in lulc_uri_dict])
    if len(vars_dict['cell_size']) == 1:
        LOGGER.debug("All rasters have the same cell size.")
        vars_dict['cell_size'] = vars_dict['cell_size'].pop()
    else:
        msg = "All rasters must have the same cell size."
        LOGGER.error(msg)
        raise ValueError, msg

    # check that all rasters are aligned
    LOGGER.debug("Checking alignment.")
    try:
        _alignment_check_uri([lulc_uri_dict[k] for k in lulc_uri_dict])
    except ValueError, msg:
        LOGGER.error("Alignment check FAILED.")
        LOGGER.error(msg)
        raise ValueError, msg
