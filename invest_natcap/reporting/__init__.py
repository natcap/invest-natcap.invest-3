"""The invest_natcap.testing package defines core testing routines and
functionality."""

import os
import logging
import csv
import json

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
            elements to be added to the html page (required). The 3 main
            element types are 'table', 'head', and 'text'.
            All elements share the following arguments:
                'type' - a string that depicts the type of element being add.
                    Currently 'table', 'head', and 'text defined (required)
                
                'section' - a string that depicts whether the element belongs
                    in the body or head of the html page. 
                    Values: 'body' | 'head' (required)
                        
                'position' - an integer that depicts where the element should
                    be placed on the html page. Elements will be written in
                    ascending order with sections 'body' and 'head' separately
                    defined (required)
            
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
                    table'key_field' (required for 'data_type' = 'shapefile' | 'csv')

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

    html_obj = {'head':{}, 'body':{}}
    
    report = {
            'table': build_table,
            'text' : add_text_element,
            'head': add_head_element
            }

    for element in reporting_args['elements']:
        
        fun_type = element.pop('type')
        section = element.pop('section')
        position = element.pop('position')
        html_obj[section][position] = report[fun_type](element)

    LOGGER.debug('HTML OBJECT : %s', html_obj)

    write_html(html_obj, reporting_args['out_uri'], reporting_args['title'])

def write_html(html_obj, out_uri, title):
    """Write an html file by parsing through a dictionary that contains strings
        and their proper structure

        html_obj - a dictionary whose keys depict the structure for the html
            page and whose values are sub dictionaries that hold the strings 
            example: {'head':{0:'string', 1:'string', 2:'string'},
                      'body':{0:'string', 1:'string', 2:'string'}}
        
        out_uri - a URI for the output html file

        title - a string represting the title of the page

        returns - nothing
    """

    # Start the string that will be written as the html file by setting the
    # title
    html_str = '<html><head><title>%s</title>' % title
    
    # Sort the head keys so that the head elements are written in the proper
    # order
    head_keys = html_obj['head'].keys()
    head_keys.sort()
    for head_key in head_keys:
        # Concatenate the output string with the head elements
        html_str += html_obj['head'][head_key]
    
    # End the head tag and start the body tag
    html_str += '</head><body>'

    # Sort the body keys so that the body elements are written in the proper
    # order
    body_keys = html_obj['body'].keys()
    body_keys.sort()
    for body_key in body_keys:
        # Concatenate the output string with the body elements
        html_str += html_obj['body'][body_key]

    # Finish the body and the html tag
    html_str += '</body></html>'

    # If the URI for the html output file exists remove it
    if os.path.isfile(out_uri):
        os.remove(out_uri)

    # Open the file, write the string and close the file
    html_file = open(out_uri, 'w')
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
                'name' - a string for the name of the column
                'editable' - a boolean that determines whether the column
                    entries can be edited
                    'columns':{'col_id_1':{'name':'product','editable':True},
                               'col_id_2':{'name':'price','editable':False},
                               ...},

            param_args['totals'] - a dictionary that if present holds information
                for a totals row. The dictionary has two keys, 'row_name' and
                'columns'. 'columns' points to a list of the column names to
                total (required)
                        'total':{'row_name':'totals', 'columns':['col_name_1']}

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
    if 'totals' in param_args:
        table_dict['totals'] = param_args['totals']
    
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
    """Generates a string that represents a html text block wrapped in
        paragraph tags

        param_args - a dictionary with the following arguments:
            
            param_args['text'] - a string

        returns - a string
    """
    
    html_str = '<p>%s</p>' % param_args['text']
    return html_str

def add_head_element(param_args):
    """Generates a string that represents a valid element in the head section of
        an html file. Currently handles 'link' and 'script' elements, where both
        the script and link point to an external source

        param_args - a dictionary that holds the following arguments:

            param_args['format'] - a string representing the type of element to
                be added. Currently : 'script', 'link'
            
            param_args['src'] - a string URI path for the external source of the
                element.

        returns - a string representation of the html head element"""

    # Get the type of element to add
    form = param_args['format']
    # Get the external file location for either the link or script reference
    src = param_args['src']

    if form == 'link':
        html_str = '<link rel=stylesheet type=text/css href=%s>' % src
    elif form == 'script':
        html_str = '<script type=text/javascript src=%s></script>' % src
    else:
        raise Exception('Currently this type of head element is not supported')

    LOGGER.debug('HEAD STRING : %s', html_str)

    return html_str
