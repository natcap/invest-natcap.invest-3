import os
import sys
import math
import webbrowser

def generate_table(table_dict, file_out_uri, css=None):
    html_file = open(file_out_uri, 'w')

    html_file.write('<html><head>')
    html_file.write('<link rel="stylesheet" type="text/css" href="table_style.css">')
    html_file.write('<script src="sorttable.js"></script>')
    html_file.write('</head><body>')

    col_headers = get_column_headers(table_dict)
    
    html_file.write('<table class="sortable"><thead><tr>')
    
    for col in col_headers:
        html_file.write('<th>%s</th>' % col)

    html_file.write('</tr></thead><tbody>')

    row_data = get_row_data(table_dict, col_headers)
   
    for row in row_data:
        html_file.write('<tr>')
        for row_data in row:
            html_file.write('<td>%s</td>' % row_data)
        html_file.write('</tr>')

    html_file.write('</tbody></table>')


    html_file.write('</body></html>')
    html_file.close()
    webbrowser.open(file_out_uri)

def get_column_headers(table_dict):
    """Iterate through the dictionary and pull out the column headers and store
        in a list

        table_dict - a dictionary representing the table

        return - a list"""


    #TODO Fill in with actual code

    return ['col_1','col_2','col_3']

def get_row_data(table_dict, col_headers):
    """Get the row data using the col_headers as keys to keep ordering and
        return a 2D list where each inner list is a row of data

        table_dict - a dictionary with the table data
        col_headers - a list of the column header names

        return - a 2D list with each inner list representing a row"""

    return [['row_1', '12', '13'], ['row_2', '22', '23'], ['row_3', '32', '33']]


def create_css_file(out_uri):
    """Write a cool css default file, has to have the sortable table definition
        it"""
    #css_file = open(out_uri, 'w')

if __name__ == "__main__":
    dict = {}
    generate_table(dict, 'table_test_html.html')
