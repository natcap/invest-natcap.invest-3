"""InVEST valuation interface module.  Informally known as the URI level."""

import os
import logging

from osgeo import gdal

import carbon_utils
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
        args['suffix'] - a string to append to any output file name (optional        args['sequest_uri'] - is a uri to a GDAL raster dataset describing the
            amount of carbon sequestered
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

    try:
        file_suffix = args['suffix']
        if not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    #These lines sets up the output directory structure for the workspace
    output_directory = os.path.join(args['workspace_dir'],'output')
    if not os.path.exists(output_directory):
        LOGGER.debug('creating directory %s', output_directory)
        os.makedirs(output_directory)

    #This defines the sequestration output raster.  Notice the 1e38 value as
    #nodata.  This is something very large that should be outside the range
    #of reasonable valuation values.
    value_seq_uri = os.path.join(output_directory, 'value_seq%s.tif' % file_suffix)

    if args['carbon_price_units'] == 'Carbon Dioxide (CO2)':
        #Cover to price per unit of Carbon do this by dividing
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

    sequest_nodata = raster_utils.get_nodata_from_uri(args['sequest_uri'])

    def value_op(sequest):
        if sequest == sequest_nodata:
            return nodata_out
        return sequest * valuation_constant

    LOGGER.debug('finished constructing valuation formula')

    LOGGER.info('starting valuation of each pixel')

    pixel_size_out = raster_utils.get_cell_size_from_uri(args['sequest_uri'])
    LOGGER.debug("pixel_size_out %s" % pixel_size_out)
    raster_utils.vectorize_datasets(
        [args['sequest_uri']], value_op, value_seq_uri,
        gdal.GDT_Float32, nodata_out, pixel_size_out, "intersection")
    LOGGER.info('finished valuation of each pixel')

    # The output html file with a table to summarize model data.
    html_uri = os.path.join(output_directory, 'summary%s.html' % file_suffix)
    _CreateHtmlSummary(html_uri, args['sequest_uri'], value_seq_uri)

def _CreateHtmlSummary(html_uri, sequest_uri, value_seq_uri):
    html = open(html_uri, 'w')
    
    html.write("<html>")
    html.write("<title>InVEST Carbon Model</title>")
    html.write("<CENTER><H1>Carbon Storage and Sequestration Model Results</H1></CENTER>")
    html.write("<table border='1', cellpadding='5'>")

    def write_row(cells):
        html.write("<tr>")
        for cell in cells:
            html.write("<td>" + str(cell) + "</td>")
        html.write("</tr>")

    column_titles = ["Change in Carbon Stocks", "Net Present Value"]
    write_row("<strong>" + title + "</strong>" for title in column_titles)

    total_seq = carbon_utils.sum_pixel_values_from_uri(sequest_uri)
    total_val = carbon_utils.sum_pixel_values_from_uri(value_seq_uri)
    write_row([total_seq, total_val])

    html.write("</table>")
    html.write("</html>")

    html.close()
