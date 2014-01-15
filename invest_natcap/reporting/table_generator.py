"""A helper module for generating html tables that are represented as Strings"""
import logging

LOGGER = logging.getLogger('invest_natcap.table_generator')

def generate_table(table_dict, attributes=None):
    """Takes in a dictionary representation of a table and generates a String of
        the the table in the form of hmtl

        table_dict - a dictionary with the following arguments:
            'cols'- a list of dictionaries that defines the column
                structure for the table (required). The order of the
                columns from left to right is depicted by the index
                of the column dictionary in the list. Each dictionary
                in the list has the following keys and values: 
                    'name' - a string for the column name (required)
                    'total' - a boolean for whether the column should be
                        totaled (required)
            
            'rows' - a list of dictionaries that represent the rows. Each
                dictionaries keys should match the column names found in 
                'cols' (required) Example:
                [{col_name_1: value, col_name_2: value, ...},
                 {col_name_1: value, col_name_2: value, ...},
                 ...]

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
        # Get a copy of the column and row lists of dictionaries
        # to pass into checkbox function
        cols_copy = list(table_dict['cols'])
        rows_copy = list(table_dict['rows'])
        # Get the updated column and row data after adding a 
        # checkbox column
        table_cols, table_rows = add_checkbox_column(cols_copy, rows_copy)
        add_checkbox_total = True
    else:
        # The column and row lists of dictionaries need to update,
        # so get the originals
        table_cols = table_dict['cols']
        table_rows = table_dict['rows']
        add_checkbox_total = False

    # Get the column headers
    col_headers = get_dictionary_values_ordered(table_cols, 'name')
    # Get a list of booleans indicating whether the above column
    # headers should be allowed to be totaled
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
                col_headers, total_cols, 'Selected Total', True)

    # Add any total rows as 'tfoot' elements in the table
    if 'total' in table_dict and table_dict['total']:
        footer_string += add_totals_row(
                col_headers, total_cols, 'Total', False)

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

def add_totals_row(col_headers, total_list, total_name, checkbox_total):
    """Construct a totals row as an html string. Creates one row element with
        data where the row gets a class name and the data get a class name if
        the corresponding column is a totalable column

        col_headers - a list of the column headers in order (required)

        total_list - a list of booleans that corresponds to 'col_headers' and
            indicates whether a column should be totaled (required)

        total_name - a string for the name of the total row, ex: 'Total', 'Sum'
            (required)

        checkbox_total - a boolean value that distinguishes whether a checkbox
            total row is being added or a regular total row. Checkbox total row
            is True. This will determine the row class name and row data class
            name

        return - a string representing the html contents of a row which should
            later be used in a 'tfoot' element"""

    # Check to determine whether a checkbox total row is being added or a
    # regular totals row
    if checkbox_total:
        row_class = 'checkTotal'
        data_class = 'checkTot'
    else:
        row_class = 'totalColumn'
        data_class = 'totalCol'

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

def get_dictionary_values_ordered(dict_list, key_name):
    """Generate a list, with values from 'key_name' found in each dictionary
        in the list of dictionaries 'dict_list'. The order of the values in the
        returned list match the order they are retrieved from 'dict_list'

        dict_list - a list of dictionaries where each dictionary has the same
            keys. Each dictionary should have at least one key:value pair
            with the key being 'key_name' (required)

        key_name - a String or Int for the key name of interest in the
            dictionaries (required)

        return - a list of values from 'key_name' in ascending order based
            on 'dict_list' keys"""

    # Initiate an empty list to store values
    ordered_value_list = []
    
    # Iterate over the list and extract the wanted value from each dictionaries
    # 'key_name'. Append the value to the new list
    for item in base_dict:
        ordered_value_list.append(item[sub_key_name])

    return ordered_value_list

def add_checkbox_column(col_list, row_list):
    """Insert a new column into the list of column dictionaries so that it
        is the second column dictionary found in the list. Also add the
        checkbox column header to the list of row dictionaries and
        subsequent checkbox value

        'col_list'- a list of dictionaries that defines the column
            structure for the table (required). The order of the
            columns from left to right is depicted by the index
            of the column dictionary in the list. Each dictionary
            in the list has the following keys and values: 
                'name' - a string for the column name (required)
                'total' - a boolean for whether the column should be
                    totaled (required)
        
        'row_list' - a list of dictionaries that represent the rows. Each
            dictionaries keys should match the column names found in 
            'col_list' (required) Example:
            [{col_name_1: value, col_name_2: value, ...},
             {col_name_1: value, col_name_2: value, ...},
             ...]

        returns - a tuple of the updated column and rows list of dictionaries
            in that order"""

    # Insert a new column dictionary in the list in the second spot
    col_list.insert(1, {'name':'Select', 'total':False})

    LOGGER.debug('Columns with Checkboxes: %s', col_list)

    # For each dictionary in the row list add a 'Select' key which
    # refers to the new column and set the value as a checkbox
    for val in row_dict:
        val['Select'] = '<input type=checkbox name=cb value=1>'

    LOGGER.debug('Rows with Checkboxes: %s', row_list)

    # Return a tuple of the updated / modified column and row list of 
    # dictionaries
    return (col_list, row_list)

def get_row_data(row_list, col_headers):
    """Construct the rows in a 2D List from the list of dictionaries,
        using col_headers to properly order the row data.

        'row_list' - a list of dictionaries that represent the rows. Each
            dictionaries keys should match the column names found in 
            'col_headers'. The rows will be ordered the same as they are found
            in the dictionary list (required) Example:
            [{'col_name_1':'9/13', 'col_name_3':'expensive',
                'col_name_2':'chips'},
             {'col_name_1':'3/13', 'col_name_2':'cheap',
                'col_name_3':'peanuts'},
             {'col_name_1':'5/12', 'col_name_2':'moderate',
                'col_name_3':'mints'}]

        col_headers - a List of the names of the column headers in order
            example : [col_name_1, col_name_2, col_name_3...]

        return - a 2D list with each inner list representing a row"""

    # Initialize a list to hold output rows represented as lists
    row_data = []

    # Iterate over each dictionary in the row_list and append the values to a
    # list in the order the keys are found in 'col_headers'. Add each generated
    # list to 'row_data'
    for row_dict in row_list:
        row = []
        for col in col_headers:
            row.append(row_dict[col])
        row_data.append(row)

    return row_data
