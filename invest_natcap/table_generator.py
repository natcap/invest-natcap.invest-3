import os
import sys
import math
import webbrowser

def generate_table(table_dict, attributes=None):
    """Takes in a dictionary representation of a table and generates a String of
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
    
    # Initialize the string that will store the html representation of the table
    table_string = ''
    # Create the table header, either with attributes or without
    if attributes != None:
        attr_keys = attributes.keys()
        attr_keys.sort()
        table_string = '<table'
        for attr in attr_keys:
            table_string = '%s %s=%s' % (table_string, attr, attributes[attr])

        table_string = table_string + '>'
    else:
        table_string = '<table>'
   
    # Get the column headers
    col_headers = get_column_headers(table_dict['cols'])
    
    # Write table header tag followed by table row tag
    table_string = table_string + '<thead><tr>'
    for col in col_headers:
        table_string += '<th>%s</th>' % col
    
    table_string = table_string + '</tr></thead>'

    row_data = get_row_data(table_dict['rows'], col_headers)
    
    table_string = table_string + '<tbody>'
   
    for row in row_data:
        table_string = table_string + '<tr>'
        for row_data in row:
            table_string = table_string + '<td>%s</td>' % row_data
        table_string = table_string + '</tr>'

    table_string = table_string + '</tbody></table>'

    return table_string

def get_column_headers(col_dict):
    """Iterate through the dictionary and pull out the column headers and store
        in a list

        table_dict - a dictionary representing the table

        return - a list"""


    #TODO Fill in with actual code
    # Initialize a list to store the column names in order
    col_list = []
    # Initialize a dictionary that will map out column ordering ids to the
    # column name so that we can properly sort the column names
    sortable_dict = {}
    
    # Loop over input dictionary and set the column's 'id' value as the key and
    # the columns name as the value
    for key, value in col_dict.iteritems():
        sortable_dict[value['id']] = key
    # Get a list of the id's from the dictionary created above
    key_ids = sortable_dict.keys()
    # Sort the list
    key_ids.sort()
    
    # Iterate over the sorted list of id's and use those to grab the column
    # names and build up the proper column name list to return
    for key_id in key_ids:
        col_list.append(sortable_dict[key_id])

    return col_list 

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
    # Get the keys of the row dictionary and sort them so that the row data is
    # built up in proper order
    row_keys = row_dict.keys()
    row_keys.sort()
    
    try:
        for key in row_keys:
            # Get the dictionary representation of a row
            row_values = row_dict[key]
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

if __name__ == "__main__":
    dict = {}
    generate_table(dict, 'table_test_html.html')
