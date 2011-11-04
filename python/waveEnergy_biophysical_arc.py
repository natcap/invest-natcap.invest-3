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
arguments = {'output_dir': gp.GetParameterAsText(0),
             'wave_base_data_uri': gp.GetParameterAsText(1),
             'analysis_area_uri': gp.GetParameterAsText(2),
             'AOI_uri': gp.GetParameterAsText(3),
             'machine_perf_uri': float(gp.GetParameterAsText(4)),
             'machine_param_uri': gp.GetParameterAsText(5),
             'dem_uri': gp.GetParameterAsText(6),
#             'valuation': gp.GetParameterAsText(7),
#             'landgridpts_uri': gp.GetParameterAsText(8),
#             'machine_econ_uri': gp.GetParameterAsText(9),
#             'number_machines': gp.GetParameterAsText(10),
#             'projection_uri': gp.GetParameterAsText(11)
             }

args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\\waveEnergy_biophysical_args.json', 'w')
args_file.writelines(json.dumps(arguments))
args_file.close()

gp.AddMessage('Starting wave energy model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\waveEnergy_biophysical.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')