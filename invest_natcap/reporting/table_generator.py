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

        table_dict - a dictionary with the following arguments:
            'cols'- a dictionary that defines the column structure for
                the table (required). The dictionary has unique numeric
                keys that determine the left to right order of the columns.
                Each key has a dictionary value with the following
                arguments:
                    'name' - a string for the column name (required)
                    'total' - a boolean for whether the column should be
                        totaled (required)

            'rows' - a dictionary with keys that have sub dictionaries as
                values. The sub dictionaries have column names that match
                the names in 'cols' as keys and the corresponding entry for
                the column/row pair as a value. (required) Example:
                {row_id_0: {col_name_1: value, col_name_2: value, ...},
                 row_id_1: {col_name_1: value, col_name_2: value, ...},
                 ...
                }
            
            'checkbox' - a boolean value for whether there should be a
                checkbox column. If True a 'selected total' row will be added
                to the bottom of the table that will show the total of the
                columns selected (optional)
            
            'total'- a boolean value for whether there should be a constant
                total row at the bottom of the table that sums the column
                values (optional)

         attributes - a dictionary with keys being valid html table attributes
             that point to proper values (optional)

        returns - a string representing an html table
    """
    
    # Initialize the string that will store the html representation of the table
    table_string = ''
    
    if attributes != None:
        table_string += '<table'
        for attr_key, attr_value in attributes.iteritems():
            table_string += ' %s=%s' % (attr_key, attr_value)

        table_string += '>'
    else:
        table_string += '<table>'

    # If checkbox column is wanted set it up
    if ('checkbox' in table_dict) and (table_dict['checkbox']):
        # Get a copy of the column and row dictionaries to pass into checkbox
        # funtion 
        cols_copy = table_dict['cols'].copy()
        rows_copy = table_dict['rows'].copy()
        # Get the updated column and row dictionaries
        table_cols, table_rows = add_checkbox_column(cols_copy, rows_copy)
        add_checkbox_total = True
    else:
        # The column and row dictionaries need to update so get the originals
        table_cols = table_dict['cols']
        table_rows = table_dict['rows']
        add_checkbox_total = False

    # Get the column headers
    col_headers = get_dictionary_values_ordered(table_cols, 'name')
    total_cols = get_dictionary_values_ordered(table_cols, 'total')

    # Write table header tag followed by table row tag
    table_string = table_string + '<thead><tr>'
    for col in col_headers:
        # Add each column header to the html string
        table_string += '<th>%s</th>' % col
   
    # Add the closing tag for the table header
    table_string += '</tr></thead>'

    # Get the row data as 2D list
    row_data = get_row_data(table_rows, col_headers)
  
    footer_string = ''

    if add_checkbox_total:
        footer_string += add_totals_row(
                col_headers, total_cols, 'Selected Total', 'checkTotal',
                'checkTot')

    # Add any total rows as 'tfoot' elements in the table
    if 'total' in table_dict and table_dict['total']:
        footer_string += add_totals_row(
                col_headers, total_cols, 'Total', 'totalColumn', 'totalCol')
    
    if not footer_string == '':
        table_string += '<tfoot>%s</tfoot>' % footer_string

    # Add the start tag for the table body
    table_string += '<tbody>'
  
    # For each data row add a row in the html table and fill in the data
    for row in row_data:
        table_string += '<tr>'
        #for row_data in row:
        for row_index in range(len(row)):
            if total_cols[row_index]:
                # Add row data
                table_string += '<td class=rowDataSd>%s</td>' % row[row_index]
            else:
                table_string += '<td>%s</td>' % row[row_index]

        table_string += '</tr>'

    # Add the closing tag for the table body and table
    table_string += '</tbody></table>'

    return table_string

def add_totals_row(col_headers, total_list, total_name, row_class, data_class):
    """Construct a totals row as an html string. Creates one row element with
        data where the row gets a class name and the data get a class name if
        the corresponding column is a totalable column
        
        col_headers - a list of the column headers in order (required)

        total_list - a list of booleans that corresponds to 'col_headers' and
            indicates whether a column should be totaled (required)

        total_name - a string for the name of the total row, ex: 'Total', 'Sum'
            (required)

        row_class - a string for the class name for the total row. Used for
            table manipulation in javascript (required)

        data_class - a string for the class name for the data elements in the
            row. Used for table manipulation in javascript (required)

        return - a string representing the html contents of a row which should
            later be used in a 'tfoot' element"""

    # Begin constructing the html string for the new totals row
    # Give the row a class name and have the first data element be the name or
    # header for that row
    html_str = '<tr class=%s><td>%s</td>' % (row_class, total_name)

    # Iterate over the number of columns and add proper row data value,
    # starting from the second column as the first columns row data value was
    # defined above
    for col_index in range(1, len(col_headers)):
        # Check to see if this columns values should be totaled
        if total_list[col_index]:
            # If column should be totaled then add a class name
            html_str += '<td class=%s>--</td>' % data_class
        else:
            # If the column should not be totaled leave off the class name
            html_str += '<td>--</td>'

    html_str += '</tr>'

    return html_str

def get_dictionary_values_ordered(base_dict, sub_key_name):
    """Generate a list, ordered from the unique keys in 'base_dict', from a
        specific value retrieved from the sub dictionaries key 'sub_key_name' 
        
        base_dict - a dictionary that has unique sortable keys where the keys
            in ascending order represent the order of the constructed list.
            Each key points to a dictionary that has at least one key:value pair
            with the key being 'sub_key_name' (required)

        return - a list of values from 'sub_key_name' in ascending order based
            on 'base_dict's keys"""
   
    # Initiate an empty list to store values
    ordered_value_list = []
    # Get a list of the keys
    keys = base_dict.keys()
    # Sort the keys so that the values can be added to the list in proper order
    keys.sort()

    for key in keys:
        # Get the desired value from each keys dictionary
        value = base_dict[key][sub_key_name]
        # Add the value to the list
        ordered_value_list.append(value)

    return ordered_value_list

def add_checkbox_column(col_dict, row_dict):
    """Insert a new column into the columns dictionary so that it is the second
        column in order of 'id'. Also add the checkbox column header to the rows
        dictionary and subsequent checkbox value

        'col_dict'- a dictionary that defines the column structure for
            the table (required). The dictionary has unique numeric
            keys that determine the left to right order of the columns.
            Each key has a dictionary value with the following
            arguments:
                'name' - a string for the column name (required)
                'total' - a boolean for whether the column should be
                    totaled (required)

        'row_dict' - a dictionary with keys that have sub dictionaries as
            values. The sub dictionaries have column names that match
            the names in 'cols' as keys and the corresponding entry for
            the column/row pair as a value. (required) Example:
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
    col_dict[check_col_id] = {'name':'Select', 'total':False}

    LOGGER.debug('Columns with Checkboxes: %s', col_dict)

    # For each row in the row dictionary add a 'Select' key which refers to the
    # new column and set the value as a checkbox
    for key, val in row_dict.iteritems():
        val['Select'] = '<input type=checkbox name=cb value=1>'
        
    LOGGER.debug('Rows with Checkboxes: %s', row_dict)

    # Return a tuple of the updated / modified column and row dictionary
    return (col_dict, row_dict) 

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
