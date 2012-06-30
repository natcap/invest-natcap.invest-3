class CSVDriverTest(unittest.TestCase):
    def setUp(self):
        self.driver = invest_natcap.fileio.CSVDriver('./data/pollination/samp_input/Guild.csv')

    def test_get_file_object():
        print self.driver.get_file_object()
