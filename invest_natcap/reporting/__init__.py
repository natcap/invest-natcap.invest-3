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
    
        reporting_args[title]
        reporting_args[elements] - a list of dictionaries that represent html
            elements: {
                        'type':'table',
                        'section': 'body',
                        'position':2,
                        'sortable':True,
                        'data_type':'shapefile'|'csv'|'dictionary',
                        'data':URI | dict,
                        'key':'key_field',
                        'columns':{'col_name_1':{'id':0,'editable':True},
                                   'col_name_2':{'id':1,'editable':False},
                                   ...},
                        'total':{'row_name':'totals', 'columns':['col_name_1']}
                        }
                        {
                        'type':'head',
                        'section': 'head',
                        'format':'script',
                        'position':2,
                        'src':'sorttable.js'
                        },
                        {
                        'type':'head',
                        'section': 'head',
                        'format':'link',
                        'position':1,
                        'src':'table_style.css'
                        }

        reporting_args[out_uri]
    """
    html_obj = {'head':{}, 'body':{}}
    
    report = {
            'table': build_table,
            'text' : add_text,
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
            
            param_args['columns'] - a dictionary where the keys are the names of
                the columns and the values are dictionaries that have the
                following attributes represented by key-value pairs (required): 
                'id' - a number that defines the order of columns
                'editable' - a boolean that determines whether the column
                    entries can be edited
                        'columns':{'col_name_1':{'id':0,'editable':True},
                                   'col_name_2':{'id':1,'editable':False},
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

    # Call generate table passing in the final dictionary and attribute
    # dictionary. Return the generate string
    return table_generator.generate_table(table_dict, attr)

def add_text():
    """

    """
    pass

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
