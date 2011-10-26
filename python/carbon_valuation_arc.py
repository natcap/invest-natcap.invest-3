import os, subprocess
import getpass
import invest_core.simplejson as json
import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")
gp.AddMessage(os.getcwd())

args_dict = {
    'output_dir': gp.GetParameterAsText(0),
    'seq_uri': gp.GetParameterAsText(1),
    'n_years': gp.GetParameterAsText(2),
    'rate_of_change': gp.GetParameterAsText(3),
    'discount_rate': gp.GetParameterAsText(4)
    }

#Save user inputs from the previous run
args_file = open('C:\Users\\' + getpass.getuser() + '\My Documents\ArcGIS\carbon_biophysical_args.json', 'w')
args_file.writelines(json.dumps(json_dict))
args_file.close()

gp.AddMessage('Starting carbon valuation model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\invest_core\\carbon_biophysical.py',
                            json.dumps(arguments)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')
