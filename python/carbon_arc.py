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
lulc_cur_year = gp.GetParameter(2) 
pool_uri = gp.GetParameterAsText(3)
lulc_fut_uri = gp.GetParameterAsText(4)
lulc_fut_year = gp.GetParameter(5)
valuation = gp.GetParameterAsText(6)


#build up the JSON dictionary for saving to disk.
json_dict = {'output_dir': output_dir,
             'lulc_cur_uri': lulc_cur_uri,
             'lulc_cur_year': lulc_cur_year,
             'pool_uri': pool_uri,
             'lulc_fut_uri': lulc_fut_uri,
             'lulc_fut_year': lulc_fut_year,
             'valuation': valuation }

args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\carbon_args.json', 'w')
args_file.writelines(json.dumps(json_dict))
args_file.close()


arguments = {'lulc_cur': lulc_cur_uri,
             'lulc_fut': lulc_fut_uri,
             'carbon_pools' : pool_uri,
             'output_dir' : output_dir,
             'lulc_cur_year' : lulc_cur_year,
             'lulc_fut_year' : lulc_fut_year}

if valuation == 'true':
    arguments['calc_value'] = True
else:
    arguments['calc_value'] = False

gp.AddMessage('Starting carbon model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\invest_core.py',
                            'carbon_core', json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
#process.wait()

#gp.overwriteoutput = 1

#gp.AddToolbox("C:\Program Files\ArcGIS\Desktop10.0\ArcToolbox\Toolboxes\Data Management Tools.tbx")
#output_layer = "buffer_layer"
#output_buffer = "output_buffer"

#gp.Buffer_analysis('C:\\Users\\jadoug06\\Desktop\\lulc_samp_cur', output_layer, "1 DecimalDegrees", "FULL", "ROUND", "NONE", "")

#gp.MakeFeatureLayer(output_buffer, output_layer)
#gp.SetParameterAsText(0, output_layer)

gp.AddMessage('Done')
