#waveEnergy_arc.py
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

#build up the JSON dictionary for saving previously used parameters to disk.
arguments = {
             'workspace_dir': gp.GetParameterAsText(0),
             'wave_data_shape_path': gp.GetParameterAsText(1),
             'global_dem': gp.GetParameterAsText(2),
             'land_gridPts_uri': gp.GetParameterAsText(3),
             'machine_econ_uri': gp.GetParameterAsText(4),
             'number__of_machines': gp.GetParameterAsText(5),
             'projection_uri': gp.GetParameterAsText(6)
             }

args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\\waveEnergy_valuation_args.json', 'w')
args_file.writelines(json.dumps(arguments))
args_file.close()

gp.AddMessage('Starting wave energy model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\waveEnergy_valuation.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')
