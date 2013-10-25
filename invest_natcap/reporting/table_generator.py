import os
import sys
import math
import webbrowser
import logging

from invest_natcap import raster_utils

LOGGER = logging.getLogger('invest_natcap.table_generator')

def generate_table(table_dict, attributes=None):
    """Takes in a dictionary representation of a table and generates a String of
        the the table in the form of hmtl

        table_dict - a dictionary with the following structure:
            {'cols': {col_id_1 : {name: col_name, sortable:True, editable:False},
                      col_id_2 : {name: col_name, sortable:True, editable:False},
                      ...
                     },
             'rows': {row_id_0: {col_name_1: value, col_name_2: value, ...},
                      row_id_1: {col_name_1: value, col_name_2: value, ...},
                     ...
                     },
             'totals': row_id_x (optional)
             'checkbox':True (optional)
             }

         attributes - a dictionary with keys being valid html table attributes
             that point to proper values

    """
    
    # Initialize the string that will store the html representation of the table
    table_string = ''
    # Create the table header, either with attributes or without
    # TODO: Handle attributes better
    if attributes != None:
        attr_keys = attributes.keys()
        attr_keys.sort()
        table_string = '<table'
        for attr in attr_keys:
            table_string = '%s %s=%s' % (table_string, attr, attributes[attr])

        table_string = table_string + '>'
    else:
        table_string = '<table>'

    # If checkbox column is wanted set it up
    if ('checkbox' in table_dict) and (table_dict['checkbox']):
        # Get a copy of the column and row dictionaries to pass into checkbox
        # funtion 
        cols_copy = table_dict['cols'].copy()
        rows_copy = table_dict['rows'].copy()
        # Get the updated column and row dictionaries
        table_cols, table_rows = add_checkbox_column(cols_copy, rows_copy)
    else:
        # The column and row dictionaries need to update so get the originals
        table_cols = table_dict['cols']
        table_rows = table_dict['rows']

    # Get the column headers
    col_headers = get_column_headers(table_cols)
    
    # Write table header tag followed by table row tag
    table_string = table_string + '<thead><tr>'
    for col in col_headers:
        # Add each column header to the html string
        table_string += '<th>%s</th>' % col
   
    # Add the closing tag for the table header
    table_string = table_string + '</tr></thead>'

    # Get the row data as 2D list
    row_data = get_row_data(table_rows, col_headers)
   
    # Add the start tag for the table body
    table_string = table_string + '<tbody>'
  
    # For each data row add a row in the html table and fill in the data
    for row in row_data:
        table_string = table_string + '<tr>'
        for row_data in row:
            # Add row data
            table_string = table_string + '<td>%s</td>' % row_data
        table_string = table_string + '</tr>'

    # Add the closing tag for the table body and table
    table_string = table_string + '</tbody></table>'

    return table_string

def add_checkbox_column(col_dict, row_dict):
    """Insert a new column into the columns dictionary so that it is the second
        column in order of 'id'. Also add the checkbox column header to the rows
        dictionary and subsequent checkbox value

        col_dict - a dictionary with column ids as keys and sub dictionary as
            its value. The sub dictionary requires a key 'name' followed by the
            columns name. An example:
            {col_id_1 : {name: col_1, sortable:True, editable:False},
             col_id_2 : {name: col_2, sortable:True, editable:False},
             ...
            }

        row_dict - a dictionary with row ids as keys and sub dictionary as its
            values. The sub dictionary requires key-value pairs for all the
            column names in 'col_dict'. An Example:
            {row_id_0: {col_name_1: value, col_name_2: value, ...},
             row_id_1: {col_name_1: value, col_name_2: value, ...},
             ...
            }

        returns - a tuple of the updated column and rows dictionaries in that
            order"""

    # Get the keys from the column dictionary which will be unique id's
    # represting the order the column should be displayed
    col_ids = col_dict.keys()
    # Sort he id's
    col_ids.sort()

    # Since the checkbox column will be added as the second column, get a list
    # of all the keys starting at the second
    col_sub = col_ids[1:]
    # Save the second key's id as this will be set to the checkbox column later
    check_col_id = col_sub[0]
    # In order to add the checkbox column in as the second row, all key id's
    # from the second on will be incremented by 1. Thus we want to reverse the
    # order of the id's so that they are changed last first, to avoid duplicate
    # id conficts
    col_sub.reverse()

    for col_id in col_sub:
        # Increment each key id by 1 and set to the formers value
        col_dict[col_id + 1] = col_dict[col_id]
        # Delete the previous key from the dictionary
        del col_dict[col_id]

    # Add the checkbox column as the second column using the old second column
    # id
    col_dict[check_col_id] = {'name':'Select'}

    LOGGER.debug('Columns with Checkboxes: %s', col_dict)

    # For each row in the row dictionary add a 'Select' key which refers to the
    # new column and set the value as a checkbox
    for key, val in row_dict.iteritems():
        val['Select'] = '<input type="checkbox" name="cb" value="1">'
        
    LOGGER.debug('Rows with Checkboxes: %s', row_dict)

    # Return a tuple of the updated / modified column and row dictionary
    return (col_dict, row_dict) 

def get_column_headers(col_dict):
    """Iterate through the dictionary and pull out the column headers and store
        in a list

        col_dict - a dictionary specifying the column defintions. Example:
            {col_id_1 : {name: col_name, sortable:True, editable:False},
             col_id_2 : {name: col_name, sortable:True, editable:False},
             ...
            }

        return - a list"""

    # Initialize a list to store the column names in order
    col_names = []

    # Get a list of the keys from the column dictionary. The keys are ids that
    # specify the order the columns should be listed
    col_ids = col_dict.keys()
    # Sort the ids so that we can return a corresponding list of column names in
    # the proper order
    col_ids.sort()

    for col_id in col_ids:
        col_names.append(col_dict[col_id]['name'])

    return col_names

def get_row_data(row_dict, col_headers):
    """Construct the rows in a 2D List from the dictionary, using col_headers to
        properly order the row data.

        row_dict - a dictionary represting the row data in the following form:
            {row_key_0: {'col_name_1':'9/13', 'col_name_3':'expensive', 
                         'col_name_2':'chips'},
             row_key_1: {'col_name_1':'3/13', 'col_name_2':'cheap', 
                         'col_name_3':'peanuts'},
             row_key_2: {'col_name_1':'5/12', 'col_name_2':'moderate', 
                         'col_name_3':'mints'}}
                         
            Where the row_keys determine the order of how the rows will be
            written and col_names match the names provided in col_headers

        col_headers - a List of the names of the column headers in order
            example : [col_name_1, col_name_2, col_name_3...]
        
        return - a 2D list with each inner list representing a row"""

    # Initialize a list to hold output rows represented as lists
    row_data = []
    
    try:
        for row_key, row_values in row_dict.iteritems():
            # Initialize a list to store our individual row values
            row = []
            # Iterate over col_headers to ensure that the row values are
            # properly placed with the correct column header
            for col in col_headers:
                # Add value of row to list
                row.append(row_values[col])
            # Add the row to the list of rows
            row_data.append(row)
    except:
        raise Exception('The dictionary is not constructed correctly')

    return row_data 

def create_css_file(out_uri):
    """Write a cool css default file, has to have the sortable table definition
        it"""
    #css_file = open(out_uri, 'w')

