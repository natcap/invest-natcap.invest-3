import unittest
import os

from numpy import testing

import fisheries
import fisheries_io

data_directory = '../../test/invest-data/Fisheries/'


class Test(unittest.TestCase):
    print "Data Directory:", data_directory
    print os.listdir(data_directory)


if __name__ == '__main__':
    unittest.main()
