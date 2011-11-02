import unittest
import timber_arc
import os, sys, subprocess
import arcgisscripting

class TestTimberArc(unittest.TestCase):
    def test_timber_model(self):

        gp = arcgisscripting.create()
        os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\invest_core\\")
        
        gp.AddMessage('Running tests ...')
        process = subprocess.Popen(['..\\..\\OSGeo4W\\gdal_python_exec_test.bat',
                                    'timber_core_test.py'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,).communicate()[0]
        
        gp.AddMessage(process)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimberArc)
    unittest.TextTestRunner(verbosity=2).run(suite)
