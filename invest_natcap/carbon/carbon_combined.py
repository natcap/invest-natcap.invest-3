"""Integrated carbon model with biophysical and valuation components."""

import logging

from invest_natcap.carbon import carbon_biophysical
from invest_natcap.carbon import carbon_valuation

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('carbon_combined')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """Run the carbon model.

    This can include the biophysical model, the valuation model, or both.

    args - a python dictionary with the following possible entries:
    'workspace_dir' - a uri to the directory where we will write output
        and intermediate files.
    'suffix' - a string to append to any output file name (optional)
    'do_biophysical' - whether to run the biophysical model
    'do_valuation' - whether to run the valuation model

    The following arguments are for the *biophysical* model:
    'lulc_cur_uri' - uri to a GDAL raster dataset for the current LULC map
    'lulc_cur_year' - year of the current LULC map (required if
        'hwp_cur_shape_uri' or 'hwp_fut_shape_uri' is present)
    'lulc_fut_uri' - uri to a raster dataset for the future LULC map.
        (for sequestration analysis)
    'lulc_redd_uri' - uri to the LULC map for the REDD scenario
        (for REDD scenario analysis)
    'lulc_fut_year' - year of the future (and REDD scenario, if applicable)
        LULC maps. (required if 'hwp_fut_shape_uri' is present)
    'carbon_pools_uri' - uri to a CSV or DBF dataset mapping carbon
        storage density to the lulc classifications specified in the
        lulc rasters. (required if 'use_uncertainty' is false)
    'carbon_pools_uncertain_uri' - as above, but has probability distribution
        data for each lulc type rather than point estimates.
        (required if 'use_uncertainty' is true)
    'do_uncertainty' - a boolean that indicates whether we should do
        uncertainty analysis. Defaults to False if not present.
    'confidence_threshold' - a number between 0 and 100 that indicates
        the minimum threshold for which we should highlight regions in the
        output raster. (required if 'do_uncertainty' is True)
    'hwp_cur_shape_uri' - current shapefile uri for harvested wood
        calculation (optional, include if calculating current lulc hwp)
    'hwp_fut_shape_uri' - Future shapefile uri for harvested wood
        calculation (optional, include if calculating future lulc hwp)


    The following arguments specify sequestration data (if the valuation
        model is run without the biophysical model):
    'sequest_uri': uri to a GDAL raster dataset describing the amount of
        carbon sequestered.
    'yr_cur' - the year at which the sequestration measurement started
    'yr_fut' - the year at which the sequestration measurement ended

    The following arguments are for the *valuation* model:
    'carbon_price_units' - a string indicating whether the price is
        in terms of carbon or carbon dioxide. Can value either as
        'Carbon (C)' or 'Carbon Dioxide (CO2)'.
    'V' - value of a sequestered ton of carbon or carbon dioxide in
        dollars per metric ton
    'r' - the market discount rate in terms of a percentage
    'c' - the annual rate of change in the price of carbon
    """
    if not args['do_biophysical'] and not args['do_valuation']:
        LOGGER.info('Neither biophysical nor valuation model selected. '
                    'Nothing left to do. Exiting.')
        return

    if args['do_biophysical']:
        LOGGER.info('Executing biophysical model.')
        biophysical_outputs = carbon_biophysical.execute(args)
    else:
        biophysical_outputs = None

    if args['do_valuation']:
        LOGGER.info('Executing valuation model.')
        valuation_args = package_valuation_args(args, biophysical_outputs)
        valuation_outputs = carbon_valuation.execute(valuation_args)
    else:
        valuation_outputs = None

    create_HTML_report(biophysical_outputs, valuation_outputs)

def package_valuation_args(args, biophysical_outputs):
    if not biophysical_outputs:
        return args

    # TODO: implement threading from one model to the other
    return args

def create_HTML_report(biophysical_outputs, valuation_outputs):
    # TODO: implement
    pass
