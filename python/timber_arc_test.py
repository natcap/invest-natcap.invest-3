import os, sys, subprocess
import arcgisscripting


gp = arcgisscripting.create()
os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\invest_core\\")
        
gp.AddMessage('Running tests ...')
process = subprocess.Popen(['..\\..\\OSGeo4W\\gdal_python_exec_test.bat',
                            'timber_core_test.py'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,).communicate()[0]
        
gp.AddMessage(process)

