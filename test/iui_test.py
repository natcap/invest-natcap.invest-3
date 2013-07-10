import unittest
import os.path
import pdb
import time

from PyQt4 import QtGui
from PyQt4.QtTest import QTest as QTest

from invest_natcap.iui import base_widgets as base_widgets

JSON_DIR = os.path.join('invest-data/test/data', 'iui', 'sample_json')
QT_APPLICATION = QtGui.QApplication([])

# This is a new exception class to make it extra clear that a test needs to be
# implemented.
class TestNotImplemented(Exception): pass

class DynamicElementTemplate(object):
    def test_is_required(self):
        """For testing whether the element is required"""
        raise TestNotImplemented

    def test_requirements_met(self):
        """For testing requirementsMet"""
        raise TestNotImplemented

    def test_get_label(self):
        """For testing the effects of get_label"""
        raise TestNotImplemented

    def test_enabledby(self):
        """A test for testing the effects of setState"""
        raise TestNotImplemented

    def test_element_state(self):
        """A test for getting/setting the element state"""
        raise TestNotImplemented

    def test_requiredif(self):
        """A test for requiredIf functionality"""
        raise TestNotImplemented

    def test_get_root(self):
        """A test to get the root element pointer."""
        raise TestNotImplemented

    def test_get_elements_dictionary(self):
        """A test for getting the elements dictionary of all contained elements"""
        raise TestNotImplemented

    def test_get_output_value(self):
        """A test for the output value if an args id is prvided"""
        raise TestNotImplemented


class DynamicGroupTemplate(DynamicElementTemplate):
    def test_create_elements(self):
        """A test to ensure that this group can creat elements."""
        raise TestNotImplemented


class DynamicPrimitiveTemplate(DynamicElementTemplate):
    def test_help_text(self):
        """A test for getting/setting helpText."""
        raise TestNotImplemented

    def test_validation(self):
        """A test to ensure validation is triggered properly"""
        raise TestNotImplemented

    def test_reset_value(self):
        """A test to ensure element value is reset properly"""
        raise TestNotImplemented

    def test_set_value(self):
        """A test to ensre that the element value can be set"""
        raise TestNotImplemented

    def test_error_message(self):
        """A test for setting the error message in the error button"""
        raise TestNotImplemented

    def test_has_warning(self):
        """A test for checking whether there is a warning message"""
        raise TestNotImplemented

    def test_default_value(self):
        """A test for checking that DynamicElements can handle default values"""
        raise TestNotImplemented


class LabeledElementTemplate(DynamicPrimitiveTemplate):
    def test_error_color(self):
        """A test for the setBGcolorSatisfied functionality."""
        raise TestNotImplemented


class DynamicTextTemplate(LabeledElementTemplate):
    def test_valid_text(self):
        """A test that valid text can be restricted."""
        raise TestNotImplemented

    def test_text_toggled(self):
        """A test for what happens when the text is changed."""
        # This test should cover what happens when there is validation and when
        # there isn't validation.
        raise TestNotImplemented


class OldContainerTest(unittest.TestCase, DynamicGroupTemplate):
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

        def assert_all(state):
            self.assertEqual(filefield.requirementsMet(), state, 'FAIL: %s' % state)
            self.assertEqual(container.isEnabled(), state, 'FAIL: %s' % state)
            self.assertEqual(label.isEnabled(), state, 'FAIL: %s' % state)

        #pdb.set_trace()
        #print container
        #container.toggleHiding(False)
        filefield.setValue('aaa')
        QTest.qWait(1000)  # qWait arg is in ms
        assert_all(True)

        filefield.setValue('')
        QTest.qWait(1000)  # qWait arg is in ms
        assert_all(False)

        filefield.setValue('aaa')
        QTest.qWait(1000)  # qWait arg is in ms
        assert_all(True)

    def test_requirements_met(self):
        """Test the container c;ass; requirementsmet value"""
        container = self.ui.allElements['container']
        # container from JSON file is collapsible.

        # Verify that the container is unchecked by default and that the
        # container is collapsible
        self.assertEqual(container.isCheckable(), True)
        self.assertEqual(container.isChecked(), False)

        # When the container is unchecked, rewuirementsMet should be False
        self.assertEqual(container.requirementsMet(), False)

        # When I check the container, requirementsMet should be True
        container.setChecked(True)
        self.assertEqual(container.requirementsMet(), True)

        # When I make the container non-collapsible (via Qt), requirementsMet
        # should remain True no matter the check state
        container.setCheckable(False)
        container.setChecked(True)
        self.assertEqual(container.requirementsMet(), True)

        container.setChecked(False)
        self.assertEqual(container.requirementsMet(), True)

    def test_is_required(self):
        container = self.ui.allElements['container']

        # A container should not be required by default.
        self.assertEqual(container.isRequired(), False)


    def test_get_root(self):
        container = self.ui.allElements['container']
        root = self.ui.allElements['test_root']

        # The conainer should be able to retrieve the root element pointer,
        # which we can also identify by the string id in allElements.
        self.assertEqual(container.getRoot(), root)

    def test_get_output_value(self):
        container = self.ui.allElements['container']

        # the container is unchecked by default
        self.assertEqual(container.value(), False)

        # If I check the checkbox, the value should change accordingly
        container.setChecked(True)
        self.assertEqual(container.value(), True)

    @unittest.skip('I think the getLabel() function is being deprecated.')
    def test_get_label(self):
        pass

    def test_get_elements_dictionary(self):
        container = self.ui.allElements['container']

        # the elements dictionary should contain the container and all the
        # elements it contains.
        elem_dict = container.getElementsDictionary()

        reg_dictionary = {
            'container': container,
            'test_label': self.ui.allElements['test_label']
        }
        self.assertEqual(elem_dict, reg_dictionary)


class FileEntryTest(unittest.TestCase):
    def test_not_required(self):
        attributes = {
            'id': 'workspace',
            'label': 'Workspace',
            'type': 'folder',
            'defaultValue': '',
        }
        element = base_widgets.FileEntry(attributes)

        # Verify that the element is not required.
        self.assertEqual(element.isRequired(), False)

        # Verify that no validation error is present.
        self.assertEqual(element.error_button.error_state, None)

        # Now, change the text, check the error state.
        QTest.keyClicks(element, '/tmp')
        QTest.qWait(500)
        self.assertEqual(element.isRequired(), False)
        self.assertEqual(element.error_button.error_state, None)

    def test_requirementsMet(self):
        attributes = {
            'id': 'workspace',
            'label': 'Workspace',
            'type': 'folder',
            'defaultValue': '',
        }
        element = base_widgets.FileEntry(attributes)
        self.assertEqual(element.requirementsMet(), False)

        element.setValue('/tmp/')
        self.assertEqual(element.requirementsMet(), True)

    def test_required(self):
        # Now, verify that when the element has the 'required' flag and it is
        # set to True, that the element is required.
        attributes = {
            'id': 'workspace',
            'label': 'Workspace',
            'type': 'folder',
            'required': True,
            'defaultValue': '',
        }
        element = base_widgets.FileEntry(attributes)
        self.assertEqual(element.has_error(), True)
        self.assertEqual(element.isRequired(), True)
        self.assertEqual(element.error_button.error_state, 'error')

        element.setValue('/tmp')
        QTest.qWait(500)
        self.assertEqual(element.has_error(), False)
        self.assertEqual(element.isRequired(), True)
        self.assertEqual(element.error_button.error_state, None)

