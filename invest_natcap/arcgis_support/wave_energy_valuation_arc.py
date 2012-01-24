import os, subprocess
import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")

gp.AddMessage('Starting wave energy valuation model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\iui\\iui_main.py',
                            'python\\iui\wave_energy_valuation.json'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')

