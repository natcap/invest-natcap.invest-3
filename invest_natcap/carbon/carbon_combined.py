"""Integrated carbon model with biophysical and valuation components."""

import collections
import logging
import os
from datetime import datetime

from invest_natcap.carbon import carbon_biophysical
from invest_natcap.carbon import carbon_valuation
from invest_natcap.carbon import carbon_utils
from invest_natcap.report_generation import html

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

    create_HTML_report(args, biophysical_outputs, valuation_outputs)

def package_valuation_args(args, biophysical_outputs):
    if not biophysical_outputs:
        return args

    if 'sequest_fut' not in biophysical_outputs:
        raise Exception(
            'Both biophysical and valuation models were requested, '
            'but sequestration was not calculated. In order to calculate '
            'valuation data, please run the biophysical model with '
            'sequestration analysis enabled. This requires a future LULC map '
            'in addition to the current LULC map.')

    args['sequest_uri'] = biophysical_outputs['sequest_fut']
    args['yr_cur'] = args['lulc_cur_year']
    args['yr_fut'] = args['lulc_fut_year']

    biophysical_to_valuation = {
        'sequest_redd': 'sequest_redd_uri',
        'conf_fut': 'conf_uri',
        'conf_redd': 'conf_redd_uri'
        }

    for biophysical_key, valuation_key in biophysical_to_valuation.items():
        try:
            args[valuation_key] = biophysical_outputs[biophysical_key]
        except KeyError:
            continue

    return args

def create_HTML_report(args, biophysical_outputs, valuation_outputs):
    html_uri = os.path.join(
        args['workspace_dir'], 'output',
        'summary%s.html' % carbon_utils.make_suffix(args))

    doc = html.HTMLDocument(html_uri, 'Carbon Results',
                            'InVEST Carbon Model Results')

    doc.write_paragraph(make_report_intro(args))

    if args['do_biophysical']:
        doc.write_header('Biophysical Results')
        doc.add(make_biophysical_table(biophysical_outputs))

    if args['do_valuation']:
        doc.write_header('Valuation Results')
        for paragraph in make_valuation_intro():
            doc.write_paragraph(paragraph)
        for table in make_valuation_tables(valuation_outputs):
            doc.add(table)

    doc.write_header('Output Files')
    doc.write_paragraph(
        'This run of the carbon model produced the following output files.')
    doc.add(make_outfile_table(
            args, biophysical_outputs, valuation_outputs, html_uri))

    doc.flush()

def make_report_intro(args):
    models = []
    for model in 'biophysical', 'valuation':
        if args['do_%s' % model]:
            models.append(model)

    return ('This document summarizes the results from running the InVEST '
            'carbon model. This run of the model involved the %s %s.' %
            (' and '.join(models),
             'models' if len(models) > 1 else 'model'))

def make_biophysical_table(biophysical_outputs):
    table = html.Table(id='biophysical_table')
    table.add_row(['Scenario', 'Total carbon<br>(Mg of carbon)',
                   'Sequestered carbon (compared to current scenario)'
                   '<br>(Mg of carbon)'],
                  is_header=True)

    for scenario in ['cur', 'fut', 'redd']:
        total_carbon_key = 'tot_C_%s' % scenario
        if total_carbon_key not in biophysical_outputs:
            continue
        total_carbon = carbon_utils.sum_pixel_values_from_uri(
            biophysical_outputs[total_carbon_key])

        sequest_key = 'sequest_%s' % scenario
        if sequest_key in biophysical_outputs:
            sequestered_carbon = carbon_utils.sum_pixel_values_from_uri(
                biophysical_outputs[sequest_key])
        else:
            sequestered_carbon = 'n/a'

        table.add_row([
                make_scenario_name(scenario,
                                   'tot_C_redd' in biophysical_outputs),
                total_carbon,
                sequestered_carbon
                ])

    return table

def make_valuation_tables(valuation_outputs):
    scenario_results = {}
    change_table = html.Table(id='change_table')
    change_table.add_row(["Scenario",
                          "Sequestered carbon<br>(Mg of carbon)",
                          "Net present value<br>(USD)"],
                         is_header=True)

    for scenario_type in ['base', 'redd']:
        try:
            sequest_uri = valuation_outputs['sequest_%s' % scenario_type]
        except KeyError:
            # We may not be doing REDD analysis.
            continue

        scenario_name = make_scenario_name(
            scenario_type, 'sequest_redd' in valuation_outputs)

        total_seq = carbon_utils.sum_pixel_values_from_uri(sequest_uri)
        total_val = carbon_utils.sum_pixel_values_from_uri(
            valuation_outputs['%s_val' % scenario_type])
        scenario_results[scenario_type] = (total_seq, total_val)
        change_table.add_row([scenario_name, total_seq, format_currency(total_val)])

        try:
            seq_mask_uri = valuation_outputs['%s_seq_mask' % scenario_type]
            val_mask_uri = valuation_outputs['%s_val_mask' % scenario_type]
        except KeyError:
            # We may not have confidence-masking data.
            continue

        # Compute output for confidence-masked data.
        masked_seq = carbon_utils.sum_pixel_values_from_uri(seq_mask_uri)
        masked_val = carbon_utils.sum_pixel_values_from_uri(val_mask_uri)
        scenario_results['%s_mask' % scenario_type] = (masked_seq, masked_val)
        change_table.add_row(['%s (confident cells only)' % scenario_name,
                              masked_seq,
                              format_currency(masked_val)])

    yield change_table

    # If REDD scenario analysis is enabled, write the table
    # comparing the baseline and REDD scenarios.
    if 'base' in scenario_results and 'redd' in scenario_results:
        comparison_table = html.Table(id='comparison_table')
        comparison_table.add_row(
            ["Scenario Comparison",
             "Difference in carbon stocks<br>(Mg of carbon)",
             "Difference in net present value<br>(USD)"],
            is_header=True)

        # Add a row with the difference in carbon and in value.
        base_results = scenario_results['base']
        redd_results = scenario_results['redd']
        comparison_table.add_row(
            ['%s vs %s' % (make_scenario_name('redd'),
                           make_scenario_name('base')),
             redd_results[0] - base_results[0],
             format_currency(redd_results[1] - base_results[1])
             ])

        if 'base_mask' in scenario_results and 'redd_mask' in scenario_results:
            # Add a row with the difference in carbon and in value for the
            # uncertainty-masked scenario.
            base_mask_results = scenario_results['base_mask']
            redd_mask_results = scenario_results['redd_mask']
            comparison_table.add_row(
                ['%s vs %s (confident cells only)'
                 % (make_scenario_name('redd'),
                    make_scenario_name('base')),
                 redd_mask_results[0] - base_mask_results[0],
                 format_currency(redd_mask_results[1] - base_mask_results[1])
                 ])

        yield comparison_table


def make_valuation_intro():
    return [
        ('<strong>Positive values</strong> in this table indicate that '
         'carbon storage increased. In this case, the positive Net Present '
         'Value represents the value of the sequestered carbon.'),
        ('<strong>Negative values</strong> indicate that carbon storage '
        'decreased. In this case, the negative Net Present Value represents '
        'the cost of carbon emission.')
        ]


def make_outfile_table(args, biophysical_outputs, valuation_outputs, html_uri):
    table = html.Table(id='outfile_table')
    table.add_row(['Filename', 'Description'], is_header=True)

    descriptions = collections.OrderedDict()

    if biophysical_outputs:
        descriptions.update(make_biophysical_outfile_descriptions(
                biophysical_outputs, args))

    if valuation_outputs:
        descriptions.update(make_valuation_outfile_descriptions(
                valuation_outputs))

    html_filename = os.path.basename(html_uri)
    descriptions[html_filename] = 'This summary file.' # dude, that's so meta

    for filename, description in sorted(descriptions.items()):
        table.add_row([filename, description])

    return table


def make_biophysical_outfile_descriptions(outfile_uris, args):
    '''Return a dict with descriptions of biophysical outfiles.'''

    def name(scenario_type):
        return make_scenario_name(scenario_type,
                                  do_redd=('tot_C_redd' in outfile_uris),
                                  capitalize=False)

    def total_carbon_description(scenario_type):
        return ('Maps the total carbon stored in the %s scenario, in '
                'Mg per grid cell.') % name(scenario_type)

    def sequest_description(scenario_type):
        return ('Maps the sequestered carbon in the %s scenario, relative to '
                'the %s scenario, in Mg per grid cell.') % (
            name(scenario_type), name('cur'))

    def conf_description(scenario_type):
        return ('Maps confident areas for carbon sequestration and emissions '
                'between the current scenario and the %s scenario. '
                'Grid cells where we are at least %.2f%% confident that '
                'carbon storage will increase have a value of 1. Grid cells '
                'where we are at least %.2f%% confident that carbon storage will '
                'decrease have a value of -1. Grid cells with a value of 0 '
                'indicate regions where we are not %.2f%% confident that carbon '
                'storage will either increase or decrease.') % (
            tuple([name(scenario_type)] + [args['confidence_threshold']] * 3))

    file_key_to_func = {
        'tot_C_%s': total_carbon_description,
        'sequest_%s': sequest_description,
        'conf_%s': conf_description
        }

    return make_outfile_descriptions(outfile_uris, ['cur', 'fut', 'redd'],
                                     file_key_to_func)

def make_valuation_outfile_descriptions(outfile_uris):
    '''Return a dict with descriptions of valuation outfiles.'''

    def name(scenario_type):
        return make_scenario_name(scenario_type,
                                  do_redd=('sequest_redd' in outfile_uris),
                                  capitalize=False)

    def value_file_description(scenario_type):
        return ('Maps the economic value of carbon sequestered between the '
                'current and %s scenarios, with values in dollars per grid '
                'cell.') % name(scenario_type)

    def value_mask_file_description(scenario_type):
        return ('Maps the economic value of carbon sequestered between the '
                'current and %s scenarios, but only for cells where we are '
                'confident that carbon storage will either increase or '
                'decrease.') % name(scenario_type)

    def carbon_mask_file_description(scenario_type):
        return ('Maps the increase in carbon stored between the current and '
                '%s scenarios, in Mg per grid cell, but only for cells where '
                ' we are confident that carbon storage will either increase or '
                'decrease.') % name(scenario_type)

    file_key_to_func = {
        '%s_val': value_file_description,
        '%s_seq_mask': carbon_mask_file_description,
        '%s_val_mask': value_mask_file_description
        }

    return make_outfile_descriptions(outfile_uris, ['base', 'redd'],
                                     file_key_to_func)


def make_outfile_descriptions(outfile_uris, scenarios, file_key_to_func):
    descriptions = collections.OrderedDict()
    for scenario_type in scenarios:
        for file_key, description_func in file_key_to_func.items():
            try:
                uri = outfile_uris[file_key % scenario_type]
            except KeyError:
                continue

            filename = os.path.basename(uri)
            descriptions[filename] = description_func(scenario_type)

    return descriptions


def make_scenario_name(scenario, do_redd=True, capitalize=True):
    names = {
        'cur': 'current',
        'fut': 'baseline' if do_redd else 'future',
        'redd': 'REDD policy'
        }
    names['base'] = names['fut']
    name = names[scenario]
    if capitalize:
        return name[0].upper() + name[1:]
    return name


def format_currency(val):
    return '%.2f' % val
