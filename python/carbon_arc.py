#carbon_arc.py
import os, sys, subprocess

try:
    import json
except ImportError:
    import invest_core.simplejson as json

import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")
gp.AddMessage(os.getcwd())

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
                            'carbon', json.dumps(arguments)])
gp.AddMessage('Waiting')
process.wait()
raw_input('Done at arc level')
gp.AddMessage('Done')
