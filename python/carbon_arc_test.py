import unittest
import arcgisscripting

class TestArcCarbonUI(unittest.TestCase):
  def test_carbon(self):
    self.gp = arcgisscripting.create()
    self.gp.SetParameterAsText(0, 'file://example/lulc_uri')
    self.gp.SetParameterAsText(1, 'file://example/pool_uri')
    self.gp.SetParameterAsText(2, 'file://example/output_uri')

    lulc_uri = gp.GetParameterAsText(0)
    pool_uri = gp.GetParameterAsText(1)
    output_uri = gp.GetParameterAsText(2)

    lulc_dictionary = {'uri'  : lulc_uri,
                       'type' :'gdal',
                       'input': True}

    pool_dictionary = {'uri'  : pool_uri,
                       'type': 'dbf',
                       'input': True}

    output_dictionary = {'uri'  : output_uri,
                         'type' : 'gdal',
                         'input': False}

    arguments = {'lulc': lulc_dictionary,
                 'carbon_pools' : pool_dictionary,
                 'output' : output_dictionary}

    gp.AddMessage('Starting carbon model')

    process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                                'python\\invest_core\\invest.py',
                                'carbon_core', json.dumps(arguments)])
    gp.AddMessage('Waiting')
    process.wait()
    gp.AddMessage('Done')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestArcCarbonUI)
    unittest.TextTestRunner(verbosity=2).run(suite)
