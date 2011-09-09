#carbon_arc.py
import os, sys, subprocess
import getpass

try:
    import json
except ImportError:
    import invest_core.simplejson as json

import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")
gp.AddMessage(os.getcwd())

output_dir = gp.GetParameterAsText(0)
lulc_cur_uri = gp.GetParameterAsText(1)
lulc_fut_uri = gp.GetParameterAsText(2)
carbon_pools_uri = gp.GetParameterAsText(3)
percentile = gp.GetParameterAsText(4)

#args['lulc_cur'] - is a GDAL raster dataset for current LULC
#args['lulc_fut'] - is a GDAL raster dataset for future LULC
#args['carbon_pools'] - is an uncertainty dictionary that maps LULC type
#args['percentile'] - cuts the output to be the top and bottom
#args['output_seq'] - a GDAL raster dataset for outputting the conservative
#args['output_map'] - a colorized map indicating the regions of

#build up the JSON dictionary for saving previously used parameters to disk.
json_dict = {'output_dir': output_dir,
             'lulc_cur_uri': lulc_cur_uri,
             'lulc_fut_uri': lulc_fut_uri,
             'carbon_pools_uri': carbon_pools_uri,
             'percentile': percentile}

args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\carbon_uncertainty_args.json', 'w')
args_file.writelines(json.dumps(json_dict))
args_file.close()

arguments = {'lulc_cur_uri': lulc_cur_uri,
             'lulc_fut_uri': lulc_fut_uri,
             'carbon_pools_uri' : carbon_pools_uri,
             'percentile' : percentile}

gp.AddMessage('Starting carbon uncertainty model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\invest_carbon_core.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')
