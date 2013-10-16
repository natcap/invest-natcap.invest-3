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
                        'position':2,
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

    """
    inter_dict = {} 
    table_dict = {} 

    # Pre-process input data if a CSV file or shapefile
    data_type = param_args['data_type']
    input_data = param_args['data']
    
    if data_type == 'shapefile':
        key = param_args['key']
        inter_dict = raster_utils.extract_datasource_table_by_key(input_data, key)
    elif data_type == 'CSV':
        key = param_args['key']
        inter_dict = raster_utils.get_lookup_from_csv(input_data, key)
    else:
        inter_dict = input_data
   
    LOGGER.debug('INTER Dict: %s', inter_dict)

    table_dict['cols'] = param_args['columns']
    
    table_dict['rows'] = inter_dict
    
    if 'totals' in param_args:
        table_dict['totals'] = param_args['totals']
    
    LOGGER.debug('TABLE Dict: %s', table_dict)
    attr = None

    if param_args['sortable']:
        attr = {"class":"sortable"}

    return table_generator.generate_table(table_dict, attr)

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


