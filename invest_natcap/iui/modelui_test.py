import unittest
import sys
from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
import modelui
import shutil
import os

FILE_BASE = os.path.dirname(os.path.abspath(__file__))
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
    def click_through_model(self, model_ui, files_to_check):
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

        missing_files = []
        for filepath in files_to_check:
            full_filepath = os.path.join(TEST_WORKSPACE, filepath)
            if not os.path.exists(full_filepath):
                missing_files.append(filepath)

        self.assertEqual(missing_files, [], 'Some expected files were not '
            'found: %s' % missing_files)

    def setUp(self):
        self.app = QtGui.QApplication(sys.argv)

    def tearDown(self):
        self.app.instance().exit()
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

        self.click_through_model(model_ui, files_to_check)

    def test_carbon(self):
        file_path = os.path.join(FILE_BASE, 'carbon_biophysical.json')
        model_ui = modelui.ModelUI(file_path, True)

        # since we need to test both carbon biophysical and valuation, we need
        # to check the checox to actually trigger the calculation of
        # sequestration so that the valuation component can be run.
        checkbox = model_ui.allElements['calc_sequestration']
        QTest.mouseClick(checkbox, Qt.MouseButton(1))

        files_to_check = [
            'Output/tot_C_cur.tif',
            'Output/sequest.tif'
        ]
        self.click_through_model(model_ui, files_to_check)


        file_path = os.path.join(FILE_BASE, 'carbon_valuation.json')
        valuation_ui = modelui.ModelUI(file_path, True)

        files_to_check = [
            'Output/value_seq.tif'
        ]
        self.click_through_model(valuation_ui, files_to_check)

if __name__ == '__main__':
    # This call to unittest.main() runs all unittests in this test suite, much
    # as we would expect Nose to do when we give it a file with tests to run.
    unittest.main()
