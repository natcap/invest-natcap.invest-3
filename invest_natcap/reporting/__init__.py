"""The invest_natcap.testing package defines core testing routines and
functionality."""

import os
import shutil
import logging
import csv
import json
import codecs

import numpy as np
from osgeo import gdal
from osgeo import ogr


from invest_natcap import raster_utils
import table_generator

LOGGER = logging.getLogger('invest_natcap.reporting')

def generate_report(reporting_args):
    """Generate an html page from the arguments given in 'reporting_args'

        reporting_args[title] - a string for the title of the html page
            (required)

        reporting_args[out_uri] - a URI to the output destination for the html
            page (required)

        reporting_args[elements] - a list of dictionaries that represent html
            elements to be added to the html page. (required) If no elements
            are provided (list is empty) a blank html page will be generated.
            The 3 main element types are 'table', 'head', and 'text'.
            All elements share the following arguments:
                'type' - a string that depicts the type of element being add.
                    Currently 'table', 'head', and 'text' are defined (required)

                'section' - a string that depicts whether the element belongs
                    in the body or head of the html page.
                    Values: 'body' | 'head' (required)

                'position' - a positive integer that depicts where the element
                    should be placed on the html page. Elements will be written
                    in ascending order with sections 'body' and 'head'
                    separately defined. If two elements have the same position,
                    the following repeated positions will be bumped up
                    (required)

            Table element dictionary has at least the following additional arguments:
                'sortable' - a boolean value for whether the tables columns
                    should be sortable (required)

                'checkbox' - a boolean value for whether there should be a
                    checkbox column. If True a 'selected total' row will be added
                    to the bottom of the table that will show the total of the
                    columns selected (optional)

                'data_type' - one of the following string values:
                    'shapefile'|'csv'|'dictionary'. Depicts the type of data
                    structure to build the table from (required)

                'data' - either a dictionary if 'data_type' is 'dictionary' or
                    a URI to a CSV table or shapefile if 'data_type' is
                    'shapefile' or 'csv' (required). If a dictionary it should
                    be formatted as follows:
                    {row_id_0: {col_name_1: value, col_name_2: value, ...},
                     row_id_1: {col_name_1: value, col_name_2: value, ...},
                     ...
                    }

                'key' - a string that defines which column or field should be
                    used as the keys for extracting data from a shapefile or csv
                    table 'key_field'.
                    (required for 'data_type' = 'shapefile' | 'csv')

                'columns'- a dictionary that defines the column structure for
                    the table (required). The dictionary has unique numeric
                    keys that determine the left to right order of the columns.
                    Each key has a dictionary value with the following
                    arguments:
                        'name' - a string for the column name (required)
                        'total' - a boolean for whether the column should be
                            totaled (required)

                'total'- a boolean value for whether there should be a constant
                    total row at the bottom of the table that sums the column
                    values (optional)

            Head element dictionary has at least the following additional arguments:
                'format' - a string representing the type of head element being
                    added. Currently 'script' (javascript) and 'link' (css
                    style) accepted (required)

                'src'- a URI to the location of the external file for either
                    the 'script' or the 'link' (required)

            Text element dictionary has at least the following additional arguments:
                'text'- a string to add as a paragraph element in the html page
                    (required)

        returns - nothing"""

    # Get the title for the hmlt page and place it in a string with html
    # title tags
    html_title = '<title>%s</title>' % reporting_args['title']

    # Initiate the html dictionary which will store all the head and body
    # elements. The 'head' and 'body' keys points to a tuple of two lists. The
    # first list holds the string representations of the html elements and the
    # second list is the corresponding 'position' of those elements. This allows
    # for proper ordering later in 'write_html'.
    # Initialize head's first element to be the title where the -1 position
    # ensures it will be the first element
    html_obj = {'head':([html_title],[-1]), 'body':([],[])}

    # A dictionary of 'types' that point to corresponding functions. When an
    # 'element' is passed in the 'type' will be one of the defined types below
    # and will execute a function that properly handles that element
    report = {
            'table': build_table,
            'text' : add_text_element,
            'head': add_head_element
            }

    # Iterate over the elements to be added to the html page
    for element in reporting_args['elements']:
        # There are 3 general purpose arguments that each element will have,
        # 'type', 'section', and 'position'. Get and remove these from the
        # elements dictionary (they should not be added weight passed to the
        # individual element functions)
        fun_type = element.pop('type')
        section = element.pop('section')
        position = element.pop('position')

        # In order to copy any script files to where the output html file is to
        # be saved, the out_uri needs to be passed along into the function that
        # handles them. As of now, the easiest / maybe best way is to add a key
        # in the 'elements' dictionary being passed along
        if fun_type == 'head':
            element['out_uri'] = reporting_args['out_uri']

        # Process the element by calling it's specific function handler which
        # will return a string. Append this to html dictionary to be written
        # in write_html
        html_obj[section][0].append(report[fun_type](element))
        # Append the position of the element to the html dictionary so the
        # elements can be written in order in write_html
        html_obj[section][1].append(position)

    LOGGER.debug('HTML OBJECT : %s', html_obj)

    # Write the html page to 'out_uri'
    write_html(html_obj, reporting_args['out_uri'])

def write_html(html_obj, out_uri):
    """Write an html file to 'out_uri' from html element represented as strings
        in 'html_obj'

        html_obj - a dictionary with two keys, 'head' and 'body', that point to
            a tuple of two lists. The first list in the tuple for each key is a
            list of the htmls elements as strings. The second is a list of the
            position those elements should be written with respect to the their
            key (required)
            example: {'head':(['elem_1', 'elem_2',...],[pos_1, pos_2,...]),
                      'body':(['elem_1', 'elem_2',...],[pos_1, pos_2,...])}

        out_uri - a URI for the output html file

        returns - nothing"""

    # Start the string that will be written as the html file
    html_str = '<html>'

    for section in ['head', 'body']:
        # Write the tag for the section
        html_str += '<%s>' % section
        # Get the list of html string elements for this section
        sect_elements = html_obj[section][0]
        # Get the list of positions for the elements
        sect_order = html_obj[section][1]

        # Check to make sure the lists are not empty because it is possible no
        # elements were were added
        if len(sect_elements) > 0 and len(sect_order) > 0:
            # The position and element string are related in the two lists by
            # the index they are found. Sorting the position order list and
            # keep the relation of the element list.
            sect_order, sect_elements = zip(*sorted(zip(sect_order, sect_elements)))

            for sect_elem in sect_elements:
                # Add each element to the html string
                html_str += sect_elem

        # Add the closing tag for the section
        html_str += '</%s>' % section

    # Finish the html tag
    html_str += '</html>'

    # If the URI for the html output file exists remove it
    if os.path.isfile(out_uri):
        os.remove(out_uri)

    # Open the file, write the string and close the file
    html_file = codecs.open(out_uri, 'wb', 'utf-8')
    html_file.write(html_str)
    html_file.close()

def build_table(param_args):
    """Generates a string representing a table in html format.

        param_args - a dictionary that has the parameters for building up the
            html table. The dictionary includes the following:

            param_args['sortable'] - a boolean value that determines whether the
                table should be sortable (required)

            param_args['data_type'] - a string depicting the type of input to
                build the table from. Either 'shapefile', 'csv', or 'dictionary'
                (required)

            param_args['data'] - a URI to a csv or shapefile OR a dictionary
                (required)

            param_args['key'] - a string that depicts which column (csv) or
                field (shapefile) will be the unique key to use in extracting
                the data into a dictionary. (required for 'data_type'
                'shapefile' and 'csv')

            param_args['columns'] - a dictionary where the keys are the ids of
                the columns (representing how the order they should be
                displayed) and the values are dictionaries that have the
                following attributes represented by key-value pairs (required):
                'name' - a string for the name of the column (required)
                'total' - a boolean that determines whether the column
                    entries should be summed in a total row (required)

            param_args['total'] - a boolean value where if True a constant
                total row will be placed at the bottom of the table that sums the
                columns (required)

        returns - a string that represents an html table
    """
    # Initialize an intermediate dictionary which will hold the physical data
    # elements of the table
    data_dict = {}

    # Initialize the final dictionary which will have the data of the table as
    # well as parameters needed to build up the html table
    table_dict = {}

    # Get the data type of the input being passed in so that it can properly be
    # pre-processed
    data_type = param_args['data_type']

    # Get a handle on the input data being passed in, whether it a URI to a
    # shapefile / csv file or a dictionary
    input_data = param_args['data']

    # Depending on the type of input being passed in, pre-process it accordingly
    if data_type == 'shapefile':
        key = param_args['key']
        data_dict = raster_utils.extract_datasource_table_by_key(input_data, key)
    elif data_type == 'csv':
        key = param_args['key']
        data_dict = raster_utils.get_lookup_from_csv(input_data, key)
    else:
        data_dict = input_data

    LOGGER.debug('Data Collected from Input Source: %s', data_dict)

    # Add the columns dictionary to the final dictionary that is to be passed
    # off to the table generator
    table_dict['cols'] = param_args['columns']

    # Add the properly formatted data dictionary to the final dictionary that is
    # to be passed to the table generator
    table_dict['rows'] = data_dict

    # If a totals row is present, add it to the final dictionary
    if 'total' in param_args:
        table_dict['total'] = param_args['total']

    LOGGER.debug('Final Table Dictionary: %s', table_dict)

    attr = None
    # If table is sortable build up a dictionary with the proper key-value pair
    if param_args['sortable']:
        attr = {"class":"sortable"}

    # If a checkbox column is wanted pass in the table dictionary
    if 'checkbox' in param_args and param_args['checkbox']:
        table_dict['checkbox'] = True

    # Call generate table passing in the final dictionary and attribute
    # dictionary. Return the generate string
    return table_generator.generate_table(table_dict, attr)

def add_text_element(param_args):
    """Generates a string that represents a html text block. The input string
        should be wrapped in proper html tags

        param_args - a dictionary with the following arguments:

            param_args['text'] - a string

        returns - a string
    """

    return param_args['text']

def add_head_element(param_args):
    """Generates a string that represents a valid element in the head section of
        an html file. Currently handles 'link' and 'script' elements, where both
        the script and link point to an external source

        param_args - a dictionary that holds the following arguments:

            param_args['format'] - a string representing the type of element to
                be added. Currently : 'script', 'link' (required)

            param_args['src'] - a string URI path for the external source of the
                element (required)
            
            param_args['out_uri'] - a string URI path for the html page
                (required)

        returns - a string representation of the html head element"""

    # Get the type of element to add
    form = param_args['format']
    # Get the external file location for either the link or script reference
    src = param_args['src']
    # The destination on disk for the html page to be written to. This will be
    # used to get the directory name so as to locate the scripts properly
    output_uri = param_args['out_uri']
    # Initialize the destination URI to be the same as how it comes in, in the
    # case where the destination URI is already in the proper directory
    #dst = src

    # Copy the source file to the location of the output directory
    # Get the script files basename
    basename = os.path.basename(src)
    # Get the output_uri directory location
    dirname = os.path.dirname(output_uri)
    # Set the destination URI for copying the script
    dst = os.path.join(dirname, basename)
    
    if not os.path.isfile(dst):
        shutil.copyfile(src, dst)

    relative_dst = './' + basename

    if form == 'link':
        html_str = '<link rel=stylesheet type=text/css href=%s>' % relative_dst
    elif form == 'script':
        html_str = '<script type=text/javascript src=%s></script>' % relative_dst
    else:
        raise Exception('Currently this type of head element is not supported')

    LOGGER.debug('HEAD STRING : %s', html_str)

    return html_str
