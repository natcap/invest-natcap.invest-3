"""InVEST valuation interface module.  Informally known as the URI level."""

import os
import logging

from osgeo import gdal

from invest_natcap.carbon import carbon_utils
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('carbon_valuation')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """This function calculates carbon sequestration valuation.
        
        args - a python dictionary with at the following *required* entries:
        
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['suffix'] - a string to append to any output file name (optional)
        args['sequest_uri'] - is a uri to a GDAL raster dataset describing the
            amount of carbon sequestered (baseline scenario, if this is REDD)
        args['sequest_redd_uri'] (optional) - uri to the raster dataset for
            sequestration under the REDD policy scenario
        args['carbon_price_units'] - a string indicating whether the price is 
            in terms of carbon or carbon dioxide. Can value either as
            'Carbon (C)' or 'Carbon Dioxide (CO2)'.
        args['V'] - value of a sequestered ton of carbon or carbon dioxide in 
            dollars per metric ton
        args['r'] - the market discount rate in terms of a percentage
        args['c'] - the annual rate of change in the price of carbon
        args['yr_cur'] - the year at which the sequestration measurement 
            started
        args['yr_fut'] - the year at which the sequestration measurement ended
        
        returns nothing."""

    # Set up the output directory structure for the workspace.
    output_directory = os.path.join(args['workspace_dir'],'output')
    if not os.path.exists(output_directory):
        LOGGER.debug('creating directory %s', output_directory)
        os.makedirs(output_directory)


    if args['carbon_price_units'] == 'Carbon Dioxide (CO2)':
        #Convert to price per unit of Carbon do this by dividing
        #the atomic mass of CO2 (15.9994*2+12.0107) by the atomic
        #mass of 12.0107.  Values gotten from the periodic table of
        #elements.
        args['V'] *= (15.9994*2+12.0107)/12.0107

    LOGGER.debug('constructing valuation formula')
    n = args['yr_fut'] - args['yr_cur'] - 1
    ratio = 1.0 / ((1 + args['r'] / 100.0) * (1 + args['c'] / 100.0))
    valuation_constant = args['V'] / (args['yr_fut'] - args['yr_cur']) * \
        (1.0 - ratio ** (n + 1)) / (1.0 - ratio)

    nodata_out = -1.0e10

    outfile_uris = _make_outfile_uris(output_directory, args)

    sequest_uris = {}
    sequest_uris['base'] = args['sequest_uri']
    if args.get('sequest_redd_uri'):
        sequest_uris['redd'] = args['sequest_redd_uri']

    conf_uris = {}
    if args.get('conf_uri'):
        conf_uris['base'] = args['conf_uri']
    if args.get('conf_redd_uri'):
        conf_uris['redd'] = args['conf_redd_uri']

    for scenario_type, sequest_uri in sequest_uris.items():
        sequest_nodata = raster_utils.get_nodata_from_uri(sequest_uri)

        def value_op(sequest):
            if sequest == sequest_nodata:
                return nodata_out
            return sequest * valuation_constant

        LOGGER.debug('finished constructing valuation formula for %s scenario' % scenario_type)
        
        LOGGER.info('starting valuation of each pixel')

        pixel_size_out = raster_utils.get_cell_size_from_uri(sequest_uri)
        LOGGER.debug("pixel_size_out %s" % pixel_size_out)
        raster_utils.vectorize_datasets(
            [sequest_uri], value_op, outfile_uris['%s_val' % scenario_type],
            gdal.GDT_Float32, nodata_out, pixel_size_out, "intersection")

        LOGGER.info('finished valuation of each pixel')

        if scenario_type in conf_uris:
            # Produce a raster for sequestration with uncertain areas masked out.
            _create_masked_raster(sequest_uri, conf_uris[scenario_type], 
                                  outfile_uris['%s_seq_mask' % scenario_type])

            # Produce a raster for value sequestration with uncertain areas masked out.
            _create_masked_raster(outfile_uris['%s_val' % scenario_type], conf_uris[scenario_type],
                                  outfile_uris['%s_val_mask' % scenario_type])

    _create_html_summary(outfile_uris, sequest_uris)

def _make_outfile_uris(output_directory, args):
    '''Set up a dict with uris for outfiles.

    Outfiles include rasters for value sequestration, confidence-masked carbon sequestration,
    confidence-masked value sequestration, and an HTML summary file.
    '''
    try:
        file_suffix = args['suffix']
        if not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    outfile_uris = {}

    # Value sequestration for base scenario.
    outfile_uris['base_val'] = os.path.join(output_directory, 'value_seq%s.tif' % file_suffix)

    # Confidence-masked rasters for base scenario.
    if args.get('conf_uri'):
        outfile_uris['base_seq_mask'] = os.path.join(output_directory, 'seq_mask%s.tif' % file_suffix)
        outfile_uris['base_val_mask'] = os.path.join(output_directory, 'val_mask%s.tif' % file_suffix)

    # Outputs for REDD scenario.
    if args.get('sequest_redd_uri'):
        # Value sequestration.
        outfile_uris['redd_val'] = os.path.join(output_directory, 'value_seq_redd%s.tif' % file_suffix)

        # Confidence-masked rasters for REDD scenario.
        if args.get('conf_redd_uri'):
            outfile_uris['redd_seq_mask'] = os.path.join(output_directory, 'seq_mask_redd%s.tif' % file_suffix)
            outfile_uris['redd_val_mask'] = os.path.join(output_directory, 'val_mask_redd%s.tif' % file_suffix)

    # HTML summary file.
    outfile_uris['html'] = os.path.join(output_directory, 'summary%s.html' % file_suffix)
    
    return outfile_uris

def _create_masked_raster(orig_uri, mask_uri, result_uri):
    '''Creates a raster at result_uri with some areas masked out.

    orig_uri -- uri of the original raster
    mask_uri -- uri of the raster to use as a mask
    result_uri -- uri at which the new raster should be created

    Masked data in the result file is denoted as no data (not necessarily zero).

    Data is masked out at locations where mask_uri is 0 or no data.
    '''
    nodata_orig = raster_utils.get_nodata_from_uri(orig_uri)
    nodata_mask = raster_utils.get_nodata_from_uri(mask_uri)
    def mask_op(orig_val, mask_val):
        if mask_val == 0 or mask_val == nodata_mask:
            return nodata_orig
        return orig_val
            
    pixel_size = raster_utils.get_cell_size_from_uri(orig_uri)
    raster_utils.vectorize_datasets(
        [orig_uri, mask_uri], mask_op, result_uri, gdal.GDT_Float32, nodata_orig,
        pixel_size, 'intersection', dataset_to_align_index=0)

def _create_html_summary(outfile_uris, sequest_uris):
    html = open(outfile_uris['html'], 'w')
    
    html.write("<html>")
    html.write("<title>InVEST Carbon Model</title>")
    html.write("<CENTER><H1>Carbon Storage and Sequestration Model Results</H1></CENTER>")
    html.write("<table border='1', cellpadding='5'>")

    def write_row(cells):
        html.write("<tr>")
        for cell in cells:
            html.write("<td>" + str(cell) + "</td>")
        html.write("</tr>")

    def write_bold_row(cells):
        write_row("<strong>" + str(cell) + "</strong>" for cell in cells)

    write_bold_row(["Scenario", "Change in Carbon Stocks", "Net Present Value"])

    scenario_names = {'base': 'Baseline', 'redd': 'REDD policy'}
    scenario_results = {}
    masked_scenario_results = {}
    for scenario_type, scenario_name in scenario_names.items():
        if scenario_type not in sequest_uris:
            # REDD scenario might not exist, so skip it.
            continue

        total_seq = carbon_utils.sum_pixel_values_from_uri(sequest_uris[scenario_type])
        total_val = carbon_utils.sum_pixel_values_from_uri(outfile_uris['%s_val' % scenario_type])
        scenario_results[scenario_type] = (total_seq, total_val)
        write_row([scenario_name, total_seq, total_val])

        if ('%s_seq_mask' % scenario_type) in outfile_uris:
            # Compute output for confidence-masked data.
            masked_seq = carbon_utils.sum_pixel_values_from_uri(
                outfile_uris['%s_seq_mask' % scenario_type])
            masked_val = carbon_utils.sum_pixel_values_from_uri(
                outfile_uris['%s_val_mask' % scenario_type])
            write_row(['%s (only confident cells)' % scenario_name, masked_seq, masked_val])

    # Compute comparison data between scenarios.
    if 'base' in scenario_results and 'redd' in scenario_results:
        write_row([' ', ' ', ' '])
        write_bold_row(["Scenario Comparison", "Difference in Carbon Stocks",
                        "Difference in Net Present Value"])
        write_row(['%s vs %s' % (scenario_names['redd'], scenario_names['base']),
                   scenario_results['redd'][0] - scenario_results['base'][0], # subtract carbon amounts
                   scenario_results['redd'][1] - scenario_results['base'][1]  # subtract value
                   ])

    html.write("</table>")
    html.write("</html>")

    html.close()
