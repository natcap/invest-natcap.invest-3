import os, subprocess
import getpass
import invest_core.simplejson as json
import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")
gp.AddMessage(os.getcwd())

#These args and names are defined on the following spreadsheet:
#https://docs.google.com/spreadsheet/ccc?key=0AqZtsmcgQETMdEREZV9NV3l6Wk5Mc0NFZGFaQ3JRUUE
args_dict = {
    'calculate_sequestration': gp.GetParameterAsText(0),
    'calculate_hwp' : gp.GetParameterAsText(1),
    'workspace_dir': gp.GetParameterAsText(2),
    'lulc_cur_uri': gp.GetParameterAsText(3),
    'lulc_fut_uri': gp.GetParameterAsText(4),
    'lulc_cur_year': gp.GetParameterAsText(5),
    'lulc_fut_year': gp.GetParameterAsText(6),
    'carbon_pools_uri': gp.GetParameterAsText(7),
    'hwp_cur_shape_uri' : gp.GetParameterAsText(8),
    'hwp_fut_shape_uri' : gp.GetParameterAsText(9)
    }

#Save user inputs from the previous run
args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\carbon_biophysical_args.json', 'w')
args_file.writelines(json.dumps(json_dict))
args_file.close()

gp.AddMessage('Starting carbon biophysical model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\carbon_biophysical.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')
