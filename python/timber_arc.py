#timber_arc.py
import os, sys, subprocess
import getpass
import json
import datetime
from datetime import date
from datetime import datetime
import time

import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")
gp.AddMessage(os.getcwd())

#build up the JSON dictionary for saving previously used parameters to disk.
arguments = {'output_dir': gp.GetParameterAsText(0),
             'timber_shp_uri': gp.GetParameterAsText(1),
             'plant_prod_uri': gp.GetParameterAsText(2),
             'market_disc_rate': float(gp.GetParameterAsText(3))}

args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\\timber_args.json', 'w')
args_file.writelines(json.dumps(arguments))
args_file.close()

gp.AddMessage('Starting timber model')

now = datetime.now()
date = now.strftime('%Y-%m-%d-%H-%M')

text_array =["TIMBER MODEL PARAMETERS",
             "_______________________\n",
             "Date and Time: "+ date,
             "Output Folder: "+ arguments['output_dir'],
             "Managed timber forest parcels: "+ arguments['timber_shp_uri'],
             "Production table: "+ arguments['plant_prod_uri'],
             "Market discount rate: "+ str(arguments['market_disc_rate']),
             "Script Location: "+ os.path.dirname(sys.argv[0])+"\\"+os.path.basename(sys.argv[0])]


filename = arguments['output_dir']+os.sep+"Timber_"+date+".txt"
file = open(filename, 'w')

for value in text_array:
    file.write(value + '\n')
    file.write('\n')

file.close()


process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\invest_timber_core.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')

#
#'header' : "TIMBER MODEL PARAMETERS",
#             'spacer' : "_______________________\n",
#             'dateAndTime' : "Date and Time: "+ date,
#             'outputFolder' : "Output Folder: "+ arguments['output_dir'],
#             'shapefileLocation' : "Managed timber forest parcels: "+ arguments['timber_shp_uri'],
#             'productionTable' : "Production table: "+ arguments['plant_prod_uri'],
#             'mdr' : "Market discount rate: "+ str(arguments['market_disc_rate']),
#             'scriptLocation' : "Script Location: "+ os.path.dirname(sys.argv[0])+"\\"+os.path.basename(sys.argv[0])