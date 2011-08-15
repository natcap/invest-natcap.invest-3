import carbon
import unittest
import unittest2 #necessary for testing on Python 2.6, included with Arc
import arcgisscripting

class TestArcCarbonUI(unittest.TestCase):
  def test_carbon(self):
    self.gp = arcgisscripting.create()
    self.gp.SetParameterAsText(0, 'file://example/lulc_uri')
    self.gp.SetParameterAsText(1, 'file://example/pool_uri')
    self.gp.SetParameterAsText(2, 'file://example/output_uri')
    carbon.carbon(gp)
    #check the result of carbon, so check to see if the output file exists and that its contents are correct
    assertTrue(False, "We'll fix this") 
#    self.assertEqual(carbon.getParameter(0, self.gp), 'file://example/lulc_uri')
#    self.assertEqual(carbon.getParameter(1, self.gp), 'file://example/pool_uri')
#    self.assertEqual(carbon.getParameter(2, self.gp), 'file://example/output_ur')
    

