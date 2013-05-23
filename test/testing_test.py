import unittest
import os

import invest_natcap.testing as testing
from invest_natcap.testing import data_storage

POLLINATION_DATA = os.path.join('data', 'pollination', 'samp_input')

class DataStorageTest(unittest.TestCase):
    def test_collect_parameters_simple(self):
        params = {
            'a': 1,
            'b': 2,
            'c': os.path.join(POLLINATION_DATA, 'LU.csv'),
        }

        archive_uri = os.path.join('data', 'test_out', 'archive')

        data_storage.collect_parameters(params, archive_uri)
