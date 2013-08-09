"""InVEST valuation interface module.  Informally known as the URI level."""

import collections
import os
import logging

from osgeo import gdal

from invest_natcap.carbon import carbon_utils
from invest_natcap import raster_utils
from invest_natcap.report_generation import html

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
        args['conf_uri'] (optional) - uri to the raster dataset indicating
            confident pixels for sequestration or emission
        args['conf_redd_uri'] (optional) - as above, but for the REDD scenario
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

    output_directory = carbon_utils.setup_dirs(args['workspace_dir'], 'output')

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
            _create_masked_raster(
                outfile_uris['%s_val' % scenario_type],
                conf_uris[scenario_type],
                outfile_uris['%s_val_mask' % scenario_type])

    _create_html_summary(outfile_uris, sequest_uris)

def _make_outfile_uris(output_directory, args):
    '''Set up a dict with uris for outfiles.

    Outfiles include rasters for value sequestration, confidence-masked carbon sequestration,
    confidence-masked value sequestration, and an HTML summary file.
    '''
    file_suffix = carbon_utils.make_suffix(args)

    def outfile_uri(prefix, scenario_type='', filetype='tif'):
        '''Create the URI for the appropriate output file.'''
        if not args.get('sequest_redd_uri'):
            # We're not doing REDD analysis, so don't append anything,
            # since there's only one scenario.
            scenario_type = ''
        elif scenario_type:
            scenario_type = '_' + scenario_type
        filename = '%s%s%s.%s' % (prefix, scenario_type, file_suffix, filetype)
        return os.path.join(output_directory, filename)

    outfile_uris = collections.OrderedDict()

    # Value sequestration for base scenario.
    outfile_uris['base_val'] = outfile_uri('value_seq', 'base')

    # Confidence-masked rasters for base scenario.
    if args.get('conf_uri'):
        outfile_uris['base_seq_mask'] = outfile_uri('seq_mask', 'base')
        outfile_uris['base_val_mask'] = outfile_uri('val_mask', 'base')

    # Outputs for REDD scenario.
    if args.get('sequest_redd_uri'):
        # Value sequestration.
        outfile_uris['redd_val'] = outfile_uri('value_seq', 'redd')

        # Confidence-masked rasters for REDD scenario.
        if args.get('conf_redd_uri'):
            outfile_uris['redd_seq_mask'] = outfile_uri('seq_mask', 'redd')
            outfile_uris['redd_val_mask'] = outfile_uri('val_mask', 'redd')

    # HTML summary file.
    outfile_uris['html'] = outfile_uri('summary', filetype='html')

    return outfile_uris

def _make_outfile_descriptions(outfile_uris):
    '''Returns a dict with descriptions of each outfile, keyed by filename.'''

    def value_file_description(scenario_name):
        return ('Maps the economic value of carbon sequestered between the '
                'current and %s scenarios, with values in dollars per grid '
                'cell.') % scenario_name

    def value_mask_file_description(scenario_name):
        return ('Maps the economic value of carbon sequestered between the '
                'current and %s scenarios, but only for cells where we are '
                'confident that carbon storage will either increase or '
                'decrease.') % scenario_name

    def carbon_mask_file_description(scenario_name):
        return ('Maps the increase in carbon stored between the current and '
                '%s scenarios, in Mg per grid cell, but only for cells where '
                ' we are confident that carbon storage will either increase or '
                'decrease.') % scenario_name

    # Adjust the name of the baseline future scenario based on whether
    # REDD analysis is enabled or not.
    if 'redd_val' in outfile_uris:
        base_name = 'baseline'
    else:
        base_name = 'future'

    redd_name = 'REDD policy'

    description_dict = {
        'base_val': value_file_description(base_name),
        'base_seq_mask': carbon_mask_file_description(base_name),
        'base_val_mask': value_mask_file_description(base_name),
        'redd_val': value_file_description(redd_name),
        'redd_seq_mask': carbon_mask_file_description(redd_name),
        'redd_val_mask': value_mask_file_description(redd_name)
        }

    descriptions = collections.OrderedDict()
    for key, uri in outfile_uris.items():
        if key == 'html':
            # Don't need a description for this summary file.
            continue
        filename = os.path.basename(uri)
        descriptions[filename] = description_dict[key]

    return descriptions

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
    doc = html.HTMLDocument(outfile_uris['html'],
                            'Carbon Model Results',
                            'InVEST Carbon Storage and Sequestration Model Results')

    def format_currency(val):
        return '%.2f' % val

    doc.write_header('Results Summary')
    doc.write_paragraph(
        '<strong>Positive values</strong> in this table indicate that carbon storage increased. '
        'In this case, the positive Net Present Value represents the value of '
        'the sequestered carbon.')
    doc.write_paragraph(
        '<strong>Negative values</strong> indicate that carbon storage decreased. '
        'In this case, the negative Net Present Value represents the cost of '
        'carbon emission.')

    # Write the table that summarizes change in carbon stocks and
    # net present value.
    change_table = doc.add(html.Table(id='change_table'))
    change_table.add_row(["Scenario",
                          "Change in Carbon Stocks<br>(Mg of carbon)",
                          "Net Present Value<br>(USD)"],
                         is_header=True)

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
        change_table.add_row([scenario_name, total_seq, format_currency(total_val)])

        if ('%s_seq_mask' % scenario_type) in outfile_uris:
            # Compute output for confidence-masked data.
            masked_seq = carbon_utils.sum_pixel_values_from_uri(
                outfile_uris['%s_seq_mask' % scenario_type])
            masked_val = carbon_utils.sum_pixel_values_from_uri(
                outfile_uris['%s_val_mask' % scenario_type])
            scenario_results['%s_mask' % scenario_type] = (masked_seq, masked_val)
            change_table.add_row(['%s (confident cells only)' % scenario_name,
                                  masked_seq,
                                  format_currency(masked_val)])

    # If REDD scenario analysis is enabled, write the table
    # comparing the baseline and REDD scenarios.
    if 'base' in scenario_results and 'redd' in scenario_results:
        comparison_table = doc.add(html.Table(id='comparison_table'))
        comparison_table.add_row(["Scenario Comparison",
                          "Difference in Carbon Stocks<br>(Mg of carbon)",
                          "Difference in Net Present Value<br>(USD)"],
                         is_header=True)
        base_results = scenario_results['base']
        redd_results = scenario_results['redd']
        comparison_table.add_row(
            ['%s vs %s' % (scenario_names['redd'], scenario_names['base']),
             redd_results[0] - base_results[0], # subtract carbon amounts
             format_currency(redd_results[1] - base_results[1])  # subtract value
             ])
        if 'base_mask' in scenario_results and 'redd_mask' in scenario_results:
            base_mask_results = scenario_results['base_mask']
            redd_mask_results = scenario_results['redd_mask']
            comparison_table.add_row(
                ['%s vs %s (confident cells only)'
                 % (scenario_names['redd'], scenario_names['base']),
                 redd_mask_results[0] - base_mask_results[0], # subtract carbon amounts
                 format_currency(redd_mask_results[1] - base_mask_results[1])  # subtract value
                 ])

    # Write a list of the output files produced by the model.
    doc.write_header('Output Files')
    outfile_descriptions = _make_outfile_descriptions(outfile_uris)

    outfile_table = doc.add(html.Table(id='outfile_table'))
    outfile_table.add_row(["Filename", "Description"], is_header=True)
    for filename, description in outfile_descriptions.items():
        outfile_table.add_row([('%s' % filename), description])

    doc.flush()
