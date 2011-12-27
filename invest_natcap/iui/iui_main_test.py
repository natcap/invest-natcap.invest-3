import sys
import unittest
from PyQt4 import QtCore, QtGui
import iui_main as iui

class TestInVESTUserInterface(unittest.TestCase):
    def test(self):
        return

class TestDynamicElement(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication(sys.argv)
    
    def testInitSmoke(self):
        """Ensure all DE object data has been initialized"""

        attributes = {}
         
        element = iui.DynamicElement(attributes)
        
        self.assertEqual(isinstance(element, QtGui.QWidget), True)
        self.assertEqual(element.attributes, attributes)
        self.assertEqual(element.root, None)
        self.assertEqual(element.required, False)
        self.assertEqual(element.enabledBy, None)
        self.assertEqual(element.elements, [])
    
    def testSetEnabledBy(self):
        """'enabledBy' attribute should be set locally if present in arg dict."""
    
        attributes = {'enabledBy': 'testElement'}
        element = iui.DynamicElement(attributes)
        
        self.assertEqual(element.enabledBy, attributes['enabledBy'])
    
    def testGetRoot(self):
        attributes = {}
        DynamicUI = iui.DynamicUI('{}')
        element = iui.DynamicElement(attributes)
        
        DynamicUI.layout().addWidget(element)
        root = element.getRoot()
        self.assertEqual(root, DynamicUI)    
    
if __name__ == '__main__':
    DynElementTests = unittest.TestLoader().loadTestsFromTestCase(TestDynamicElement)
    unittest.TextTestRunner(verbosity=2).run(DynElementTests)