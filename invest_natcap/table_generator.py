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
        table_string = '<table'
        for attr, val in attributes.iteritems():
            table_string = '%s %s=%s' % (table_string, attr, val)

        table_string = table_string + '>'
    else:
        table_string = '<table>'
   
    # Get the column headers
    col_headers = get_column_headers(table_dict['cols'])
    
    # Write table header tag followed by table row tag
    table_string = table_string + '<thead><tr>'
    for col in col_headers:
        html_file.write('<th>%s</th>' % col)
    
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
    """Get the row data using the col_headers as keys to keep ordering and
        return a 2D list where each inner list is a row of data

        table_dict - a dictionary with the table data
        col_headers - a list of the column header names

        return - a 2D list with each inner list representing a row"""

    row_data = []

    for key, value in row_dict.iteritems():
        for col in col_headers:
            row = []

    

    return [['row_1', '12', '13'], ['row_2', '22', '23'], ['row_3', '32', '33']]


def create_css_file(out_uri):
    """Write a cool css default file, has to have the sortable table definition
        it"""
    #css_file = open(out_uri, 'w')

if __name__ == "__main__":
    dict = {}
    generate_table(dict, 'table_test_html.html')
