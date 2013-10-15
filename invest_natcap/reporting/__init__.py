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
                        'sortable':True,
                        'data':{'dictionary':{},
                                'shapefile':{'uri':'path.shp',
                                            'key':'key_field'},
                                'csv':{'uri':'path.csv', 'key':'key_field'}
                        'position':2
                        },
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
            'head': add_head
            }

    for element in reporting_args['elements']:
        
        fun_type = element['type']
        section = element['section']
        position = element['position']
        html_obj[section][position] = report[fun_type](element)

    LOGGER.debug('HTML OBJECT : %s', html_obj)

    html_str = write_html(
            html_obj, reporting_args['out_uri'], reporting_args['title'])
    return html_str

def write_html(html_obj, out_uri, title):
    """

    """

    html_str = '<html><head><title>%s</title>' % title
    
    # Write head elements
    head_keys = html_obj['head'].keys()
    head_keys.sort()
    for head_key in head_keys:
        html_str += html_obj['head'][head_key]

    html_str += '</head><body>'

    # Write body elements
    body_keys = html_obj['body'].keys()
    body_keys.sort()
    for body_key in body_keys:
        html_str += html_obj['body'][body_key]

    html_str += '</body>'

    html_str += '</html>'

    if os.path.isfile(out_uri):
        os.remove(out_uri)

    html_file = open(out_uri, 'w')
    html_file.write(html_str)
    html_file.close()

    return html_str

def initialize_html_string():
    """
    {
        'head':{
            0: ''
            1: ''
            2: ''
               }
        'body':{
            0: ''
            1: ''
            2: ''
               }
    }
    
    """
    html_str = '<html>'


def build_table(param_args):
    """
def generate_table(table_dict, attributes=None):
    Takes in a dictionary representation of a table and generates a String of
        the the table in the form of hmtl

        table_dict - a dictionary with the following structure:
            {'cols': {col_name_1 : {id: 0, sortable:True, editable:False},
                      col_name_2 : {id: 1, sortable:True, editable:False},
                      ...
                     },
             'rows': {row_id_0: {
                        values: {col_name_1: value, col_name_2: value, ...},
                        sortable: False},
                      row_id_1: {
                        values: {col_name_1: value, col_name_2: value, ...},
                        sortable: False},
                     ...
                     },
             'totals': row_id_x
             }

         attributes - a dictionary with keys being valid html table attributes
             that point to proper values

    """
    table_dict = None

    # Pre-process input data if a CSV file or shapefile
    data_type = param_args['data'].keys()
    input_data = param_args['data'][data_type]
    
    if data_type == 'shapefile':
        key = input_data['key']
        table_dict = table_generator.process_table_input_shape(input_data, key)
    elif data_type == 'CSV':
        key = input_data['key']
        table_dict = table_generator.process_table_input_csv(input_data, key)
    else:
        table_dict = input_data
    
    return table_generator.generate_table(table_dict)


def add_text():
    """

    """
    pass

def add_head(param_args):
    """

    """

    form = param_args['format']
    src = param_args['src']
 
    html_str = '' 
    #html_file.write('<link rel="stylesheet" type="text/css" href="table_style.css">')

    if form == 'link':
        html_str = '<link rel=stylesheet type=text/css href=%s>' % src

    LOGGER.debug('LINK STRING : %s', html_str)

    return html_str


