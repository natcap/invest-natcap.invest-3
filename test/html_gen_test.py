'''Unit test for the HTML generation utils in report_generation.html'''

import unittest

from bs4 import BeautifulSoup

from invest_natcap.report_generation import html

FILE_PATH = 'test.html'
TITLE = 'My Test Page'
HEADER = 'This page is a test of HTML generation.'

class TestHTMLGeneration(unittest.TestCase):

    def setUp(self):
        self.doc = html.HTMLDocument(FILE_PATH, TITLE, HEADER)

    def tearDown(self):
        try:
            os.remove(FILE_PATH)
        except:
            pass

    def check_soup(self):
        '''Check some basic properties, and return the BeautifulSoup object.'''
        soup = BeautifulSoup(open(FILE_PATH, 'r').read())
        self.assertEqual(TITLE, soup.title.text)

        self.assert_contains(soup, 1, 'h1', text=HEADER)

        return soup

    def assert_contains(self, soup, num, *args, **kwargs):
        '''Assert that the given soup contains num matching elements.'''
        found = soup.find_all(*args, **kwargs)
        self.assertEqual(num, len(found))
        return found

    def test_basic_doc(self):
        '''Test basic functionality.'''
        self.doc.flush()
        self.check_soup()

    def test_writing(self):
        '''Test basic writing, and the Table of Contents.'''
        self.doc.insert_table_of_contents()

        headers = ['Cows', 'Horses']
        paragraphs = ['Cows are slow', 'Horses are fast']
        for i in range(len(headers)):
            self.doc.write_header(headers[i])
            self.doc.write_paragraph(paragraphs[i])

        self.doc.flush()

        # Verify basic properties.
        soup = self.check_soup()

        # Verify the text.
        for header in headers:
            self.assert_contains(soup, 1, 'h2', text=header)

        for paragraph in paragraphs:
            self.assert_contains(soup, 1, 'p', text=paragraph)

        # Verify that the Table of Contents was rendered correctly.
        self.assert_contains(soup, 1, 'h2', text='Table of Contents')[0]
        link_list = self.assert_contains(soup, 1, 'ul')[0]
        for header in headers:
            self.assert_contains(link_list, 1, 'li', text=header)

    def test_table(self):
        table = self.doc.add(html.Table(id='test_table'))
        header_row = ['TV Show', 'Quality']
        data_rows = [['Breaking Bad', 'Good'],
                     ['The Bachelorette', 'Bad']]
        table.add_row(header_row, is_header=True)
        for row in data_rows:
            table.add_row(row)

        self.doc.flush()

        soup = self.check_soup()

        # Check that there's a table with a header row and data rows.
        table_soup = self.assert_contains(soup, 1, 'table', id='test_table')[0]
        row_soups = table_soup.find_all('tr')
        self.assertEqual(1 + len(data_rows), len(row_soups))

        # Check that the header row is correct.
        for cell_header in header_row:
            self.assert_contains(row_soups[0], 1, 'th', text=cell_header)

        # Check that the data rows are correct.
        data_row_soups = row_soups[1:]
        for row_index, row in enumerate(data_rows):
            for cell_data in row:
                self.assert_contains(
                    data_row_soups[row_index], 1, 'td', text=cell_data)
