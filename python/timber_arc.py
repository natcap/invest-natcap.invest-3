import os, subprocess
import arcgisscripting
gp = arcgisscripting.create()

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\..\\")

gp.AddMessage('Starting timber model')

process = subprocess.Popen(['OSGeo4W\\gdal_python_exec.bat',
                            'python\\iui\\iui_main.py',
                            'python\\iui\\timber.json'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).communicate()[0]

gp.AddMessage(process)
gp.AddMessage('Done')
