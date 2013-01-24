import unittest
import sys
from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
import modelui
import shutil
import os

TEST_WORKSPACE = '/tmp/test_workspace'

# Define a new exception class for when the worspace args_id is not found in the
# json definition
class WorkspaceNotFound(Exception): pass

def locate_workspace_element(ui):
    for element_id, element in ui.allElements.iteritems():
        try:
            args_id = element.attributes['args_id']
        except KeyError:
            # A KeyError is triggered when the element doesn't have an args_id.
            pass

        # If the retrieved arg id is the definde workspace, return the element.
        if args_id == 'workspace_dir':
            return element

    # If we can't find the workspace dir element, raise a helpful exception
    # indicating that it must be clearly identifiable.
    raise WorkspaceNotFound('The workspace must be identified by the '
        'args_id "workspace_dir"')

class ModelUITest(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication(sys.argv)

    def tearDown(self):
        try:
            # Remove the workspace directory for the next test.
            shutil.rmtree(TEST_WORKSPACE)
        except OSError:
            # Thrown when there's no workspace to remove.
            pass

    def test_pollination(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(file_path, 'pollination.json')
        model_ui = modelui.ModelUI(file_path, True)

        workspace_element = locate_workspace_element(model_ui)

        workspace_element.setValue(TEST_WORKSPACE)
        QTest.qWait(100)  # Wait for the test workspace to validate

        # Assert that the test workspace didn't get a validation error.
        self.assertEqual(workspace_element.has_error(), False)

        # Assert that there are no default data validation errors.
        validation_errors = model_ui.errors_exist()
        self.assertEqual(validation_errors, [], 'Validation errors '
            'exist for %s inputs. Errors: %s' % (len(validation_errors),
            validation_errors))

        # Click the 'Run' button and see what happens now.
        QTest.mouseClick(model_ui.runButton, Qt.MouseButton(1))

        # Now that the run button has been pressed, we need to check the state
        # of the operation dialog to see if it has finished completing.  This
        # check is done at half-secong intervals.
        while not model_ui.operationDialog.backButton.isEnabled():
            QTest.qWait(500)

        # Once the test has finished, click the back button on the dialog to
        # return toe the UI.
        QTest.mouseClick(model_ui.operationDialog.backButton, Qt.MouseButton(1))

        files_to_check = [
            'intermediate/frm_Apis_cur.tif',
            'intermediate/hf_Apis_cur.tif',
            'intermediate/hn_Apis_cur.tif',
            'intermediate/sup_Apis_cur.tif',
            'intermediate/frm_Bombus_cur.tif',
            'intermediate/hf_Bombus_cur.tif',
            'intermediate/hn_Bombus_cur.tif',
            'intermediate/sup_Bombus_cur.tif',
            'output/frm_avg_cur.tif',
            'output/sup_tot_cur.tif'
        ]

        missing_files = []
        for filepath in files_to_check:
            full_filepath = os.path.join(TEST_WORKSPACE, filepath)
            if not os.path.exists(full_filepath):
                missing_files.append(filepath)

        self.assertEqual(missing_files, [], 'Some expected files were not '
            'found: %s' % missing_files)


if __name__ == '__main__':
    # This call to unittest.main() runs all unittests in this test suite, much
    # as we would expect Nose to do when we give it a file with tests to run.
    unittest.main()
