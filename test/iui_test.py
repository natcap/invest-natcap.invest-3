import unittest
import os.path
import pdb
import time

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
        # Steps to check:
        # 0.  Verify that the container is disabled
        # 1.  Put something in the file field.
        # 2.  Verify that the container is enabled
        # 3.  Remove the contents of the file field
        # 4.  Verify that the container is disabled.

        # So this test is pretty frustrating, hence all the jumbled print
        # statements.  The UI works properly (as far as I can tell) if I run
        # this through PDB __OR__ if I run the sample container as a normal UI
        # through modelui.py.  If I just run the test, the container is _always_
        # disabled.
        #
        # I suspect that once I figure this issue out, I should be in a much
        # better position to test things in the UI.

        container = self.ui.allElements['container']
        label = self.ui.allElements['test_label']
        filefield = self.ui.allElements['test_file']
        #pdb.set_trace()
        #print container
        print 'enabled %s' % container.isEnabled()
        #container.toggleHiding(False)
        print 'SETTING VALUE'
        filefield.setValue('aaa')
        time.sleep(1)
        print 'filefield requirements met: %s' % filefield.requirementsMet()
        print 'container enabled %s' % container.isEnabled()
        print 'label enabled: %s' % label.isEnabled()
        print 'filefield value %s' % filefield.value()
        print 'SETTING VALUE'
        filefield.setValue('')
        time.sleep(1)
        print 'filefield requirements met: %s' % filefield.requirementsMet()
        print 'container enabled %s' % container.isEnabled()
        print 'label enabled: %s' % label.isEnabled()
