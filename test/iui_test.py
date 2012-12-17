import unittest
import os.path

from PyQt4 import QtGui

from invest_natcap.iui import base_widgets as base_widgets

JSON_DIR = os.path.join('data', 'iui', 'sample_json')

class ContainerTest(unittest.TestCase):
    def setUp(self):
        container_test = os.path.join(JSON_DIR, 'test_container.json')

        # NEED TO FINISH THIS CALL!
        self.app = QtGui.QApplication([])
        self.ui = base_widgets.ExecRoot(container_test)

    def test_outside_element_toglling_container(self):
        print self.ui
