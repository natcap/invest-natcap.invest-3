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
        QTest.qWait(1000)  # wait for a model dialog to pop up


if __name__ == '__main__':
    # This call to unittest.main() runs all unittests in this test suite, much
    # as we would expect Nose to do when we give it a file with tests to run.
    unittest.main()
