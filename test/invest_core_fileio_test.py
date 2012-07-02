import unittest
import invest_natcap.invest_core.fileio

GUILDS_URI = './data/iui/Guild.csv'

class CSVDriverTest(unittest.TestCase):
    def setUp(self):
        print ''
        self.driver = invest_natcap.invest_core.fileio.CSVDriver(GUILDS_URI)

    def test_get_file_object(self):
        print self.driver.get_file_object()

    def test_get_fieldnames(self):
        print self.driver.get_fieldnames()

    def test_read_table(self):
        print self.driver.read_table()

class TableHandlerTest(unittest.TestCase):
    def setUp(self):
        print ''  # print a newline before each test.  makes printing prettier
        self.handler = invest_natcap.invest_core.fileio.TableHandler(GUILDS_URI)

    def test_get_table(self):
        table = self.handler.get_table()
        for row in table:
            print row

    def test_set_field_mask(self):
        self.handler.set_field_mask('^fs_', 3)
        for row in self.handler.table:
            print row

