'''Useful functions for testing HTML output.'''
from bs4 import BeautifulSoup

def assert_contains_matching_elems(test_case, uri, elems):
    '''Assert that the file contains the given elements.

    elems - a list of Element objects from the report_generation.html module.
    '''
    soup = _make_soup(uri)
    for elem in elems:
        test_case.assertIsNotNone(soup.find(elem.tag, attrs=elem.attrs))

def assert_table_contains_rows_uri(test_case, uri, table_id, rows, num_header_rows=0):
    '''Assert that the table in the file contains the given rows.

    rows - a list of rows, each of which is represented as a list
        (of cell contents).
    '''
    soup = _make_soup(uri)
    tables = soup.find_all('table', id=table_id)
    test_case.assertEqual(1, len(tables))
    table = tables[0]
    for i, row in enumerate(rows):
        is_header = (i < num_header_rows)
        _assert_table_contains_row(test_case, table, row, is_header)

def _make_soup(uri):
    return BeautifulSoup(open(uri, 'r').read())

def _assert_table_contains_row(test_case, table, row, is_header):
    ''' Asserts that the BeautifulSoup table contains the given row.'''
    for curr_row in table.find_all('tr'):
        cell_tag = 'th' if is_header else 'td'
        cells = curr_row.find_all(cell_tag)
        if len(cells) != len(row):
            # This row doesn't match; keep looking.
            continue

        row_match = True
        for i in range(len(cells)):
            if cells[i].text != str(row[i]):
                # This cell doesn't match; go on to the next row.
                row_match = False
                break

        if row_match:
            # We found a row where each cell matches.
            return

    test_case.fail(
        'No match found for row %s in table %s. The table is: %s' % (
            str(row), table['id'], str(table)))

